using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Platform;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CloudGlyph.Models;
using CloudGlyph.Services;

namespace CloudGlyph.ViewModels;

public sealed record LanguageOption(string Code, string DisplayName);

public partial class DocumentViewModel : ObservableObject
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    /// <summary>How long the query must sit still before a search runs, while the reader types.</summary>
    private static readonly TimeSpan SearchDebounce = TimeSpan.FromMilliseconds(120);

    public const string DefaultLanguage = "en";

    private List<LanguageOption> _loadedLanguages = [];

    private string _previousQuery = string.Empty;
    private WikiSearchIndex? _index;
    private CancellationTokenSource? _indexCts;
    private CancellationTokenSource? _searchCts;

    /// <summary>Full language list loaded from the auto-generated languages_index.json.</summary>
    public IReadOnlyList<LanguageOption> AllLanguages => _loadedLanguages;

    /// <summary>All available languages shown in the document-language selector on the left toolbar.</summary>
    public IReadOnlyList<LanguageOption> TopLanguages => _loadedLanguages.Count > 0
        ? _loadedLanguages
        : [new(DefaultLanguage, "🌐 English")];

    [ObservableProperty]
    private ObservableCollection<PageNode> _nodes = [];

    [ObservableProperty]
    private PageNode? _selectedNode;

    [ObservableProperty]
    private string _content = string.Empty;

    [ObservableProperty]
    private string _language = DefaultLanguage;

    [ObservableProperty]
    private LanguageOption _selectedLanguage = new(DefaultLanguage, "🌐 English");

    [ObservableProperty]
    private string _title = "Cloud Glyph";

    [ObservableProperty]
    private bool _isLoading;

    /// <summary>Text of the sidebar search box. Changing it schedules a debounced search.</summary>
    [ObservableProperty]
    private string _query = string.Empty;

    /// <summary>Raised while the search index for the current language is being built.</summary>
    [ObservableProperty]
    private bool _isIndexing;

    /// <summary>Ranked matches for <see cref="Query"/>, best first.</summary>
    public ObservableCollection<SearchHit> Results { get; } = [];

    /// <summary>Picked result. Selecting one navigates and clears the query, so it resets to null.</summary>
    [ObservableProperty]
    private SearchHit? _selectedResult;

    /// <summary>True once a query is typed — the results panel is showing.</summary>
    public bool ShowResults => !string.IsNullOrWhiteSpace(Query);

    /// <summary>
    /// Whether the results popup is open. It is two-way because the popup closes itself on a click
    /// outside or Esc; that has to clear the query, or the panel would reappear on the next keystroke
    /// with no way to dismiss it.
    /// </summary>
    [ObservableProperty]
    private bool _isSearchOpen;

    /// <summary>True when the current query matched nothing, so the sidebar can say so.</summary>
    public bool HasNoResults => ShowResults && !IsIndexing && Results.Count == 0;

    public DocumentViewModel()
    {
        Results.CollectionChanged += (_, _) =>
        {
            OnPropertyChanged(nameof(HasNoResults));
            OnPropertyChanged(nameof(ResultsHeader));
        };
        _ = InitializeAsync();
    }

    /// <summary>Result-count line above the list, e.g. "12 matches".</summary>
    public string ResultsHeader => Results.Count switch
    {
        0 => "No matches",
        1 => "1 match",
        var n => $"{n} matches",
    };

    private async Task InitializeAsync()
    {
        await LoadSiteConfigAsync();
        await LoadLanguagesAsync();
        await LoadTreeAsync();
    }

    /// <summary>
    /// Reads the site title from <c>Assets/Docs/config/site.json</c> (e.g. the product name shown in
    /// the window title). Falls back to the default <see cref="Title"/> if the asset is absent.
    /// A child wiki repo should edit its own site.json — never hardcode a product name in code.
    /// </summary>
    private async Task LoadSiteConfigAsync()
    {
        try
        {
            var uri = new Uri("avares://CloudGlyph/Assets/Docs/config/site.json");
            using var stream = AssetLoader.Open(uri);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            var json = await reader.ReadToEndAsync();
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.TryGetProperty("title", out var title) && title.ValueKind == JsonValueKind.String)
            {
                var value = title.GetString();
                if (!string.IsNullOrWhiteSpace(value))
                    Title = value.Trim();
            }
        }
        catch
        {
            // Asset missing/malformed → keep the default Title.
        }
    }

    partial void OnSelectedLanguageChanged(LanguageOption value)
    {
        if (value is null) return;
        if (!string.Equals(Language, value.Code, StringComparison.OrdinalIgnoreCase))
        {
            Language = value.Code;
            _ = ReloadAsync();
        }
    }

    partial void OnSelectedNodeChanged(PageNode? value)
    {
        if (value is not null)
            _ = LoadContentAsync(value);
    }

    partial void OnQueryChanged(string value)
    {
        // Reopening after a dismissal: the popup still holds the previous search's rows, which
        // would otherwise flash until the debounced search replaces them. Clearing on this
        // transition — not on every keystroke — keeps the list from blinking empty as you type.
        var reopening = string.IsNullOrWhiteSpace(_previousQuery) && !string.IsNullOrWhiteSpace(value);
        _previousQuery = value;
        if (reopening)
            Results.Clear();

        OnPropertyChanged(nameof(ShowResults));
        OnPropertyChanged(nameof(HasNoResults));
        IsSearchOpen = !string.IsNullOrWhiteSpace(value);
        QueueSearch(value);
    }

    partial void OnIsSearchOpenChanged(bool value)
    {
        // Dismissed (Esc, click outside, or a picked result): drop the query. Setting the same
        // value twice is a no-op, so the pair cannot loop.
        if (!value && !string.IsNullOrWhiteSpace(Query))
            Query = string.Empty;
    }

    partial void OnIsIndexingChanged(bool value) => OnPropertyChanged(nameof(HasNoResults));

    partial void OnSelectedResultChanged(SearchHit? value)
    {
        if (value is null)
            return;

        // Clicking a row lands here from inside the ListBox's own selection commit
        // (`OnPointerPressed` → `UpdateSelection` → `SelectionChanged`), and navigating closes the
        // popup — a separate window — while that commit is open. Deferring keeps that teardown off
        // the control's input path. (The crash this was first written for was the collection reset
        // in QueueSearch, which is gone; what remains is the defence against closing the popup
        // from inside its own item's input handling, which headless cannot exercise.)
        Dispatcher.UIThread.Post(() =>
        {
            if (!ReferenceEquals(SelectedResult, value))
                return;                  // a later click superseded this one
            NavigateTo(value);
            SelectedResult = null;
        });
    }

    /// <summary>
    /// Loads the auto-generated <c>languages_index.json</c> from assets and populates
    /// <see cref="AllLanguages"/>, <see cref="TopLanguages"/>.
    /// Falls back to English-only if the asset is unavailable.
    /// </summary>
    private async Task LoadLanguagesAsync()
    {
        try
        {
            var uri = new Uri("avares://CloudGlyph/Assets/Docs/content/languages_index.json");
            using var stream = AssetLoader.Open(uri);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            var json = await reader.ReadToEndAsync();

            var entries = JsonSerializer.Deserialize<List<LanguageEntry>>(json, JsonOptions);
            _loadedLanguages = entries?
                .Select(e => new LanguageOption(e.Code, $"🌐 {e.DisplayName}"))
                .ToList() ?? [];

            if (_loadedLanguages.Count > 0)
            {
                // Ensure current selection points to a valid entry in the loaded list
                if (!_loadedLanguages.Any(l => l.Code == SelectedLanguage.Code))
                    SelectedLanguage = _loadedLanguages[0];
            }
        }
        catch
        {
            // Fallback: at least show the default language
            _loadedLanguages = [new(DefaultLanguage, "🌐 English")];
        }
        finally
        {
            OnPropertyChanged(nameof(TopLanguages));
        }
    }

    private async Task LoadTreeAsync()
    {
        IsLoading = true;
        try
        {
            var code = string.IsNullOrWhiteSpace(Language) ? DefaultLanguage : Language.ToLowerInvariant();
            var uri = new Uri($"avares://CloudGlyph/Assets/Docs/content/{code}/tree.json");

            string json;
            try
            {
                using var stream = AssetLoader.Open(uri);
                using var reader = new StreamReader(stream, Encoding.UTF8);
                json = await reader.ReadToEndAsync();
            }
            catch (FileNotFoundException)
            {
                // Fall back to default language
                var fallback = new Uri($"avares://CloudGlyph/Assets/Docs/content/{DefaultLanguage}/tree.json");
                using var stream = AssetLoader.Open(fallback);
                using var reader = new StreamReader(stream, Encoding.UTF8);
                json = await reader.ReadToEndAsync();
            }

            var tree = JsonSerializer.Deserialize<TreeRoot>(json, JsonOptions);
            Nodes = BuildTree(tree?.Pages ?? []);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Failed to load tree: {ex.Message}");
            Nodes = [];
        }
        finally
        {
            IsLoading = false;
        }

        // Auto-select first node
        if (Nodes.Count > 0)
            SelectedNode = Nodes[0];

        StartIndexBuild();
    }

    private async Task ReloadAsync()
    {
        Content = string.Empty;
        SelectedNode = null;
        Query = string.Empty;
        Results.Clear();
        await LoadTreeAsync();
    }

    private async Task LoadContentAsync(PageNode node)
    {
        IsLoading = true;
        try
        {
            var markdown = await ReadPageAsync(node.Path);

            // If the page has no real content and has children,
            // auto-redirect to the first child page.
            if (string.IsNullOrWhiteSpace(markdown) && node.Children.Count > 0)
            {
                var child = node.Children[0];
                child.ExpandAncestors();
                SelectedNode = child;
                return;
            }

            Content = markdown ?? $"# {node.Title}\n\n*Content not available in this language.*";
        }
        catch (Exception ex)
        {
            Content = $"# Error\n\nFailed to load content: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>Reads a page's Markdown from the bundled assets, or <see langword="null"/> when absent.</summary>
    private async Task<string?> ReadPageAsync(string pagePath)
    {
        var code = string.IsNullOrWhiteSpace(Language) ? DefaultLanguage : Language.ToLowerInvariant();
        var uri = new Uri($"avares://CloudGlyph/Assets/Docs/content/{code}/{pagePath.Replace('\\', '/')}/index.md");
        try
        {
            using var stream = AssetLoader.Open(uri);
            using var reader = new StreamReader(stream, Encoding.UTF8);
            return await reader.ReadToEndAsync();
        }
        catch (FileNotFoundException)
        {
            return null;
        }
    }

    private static ObservableCollection<PageNode> BuildTree(List<TreePage>? pages, PageNode? parent = null)
    {
        var result = new ObservableCollection<PageNode>();
        if (pages is null) return result;

        foreach (var page in pages)
        {
            var node = new PageNode
            {
                Title = page.Title,
                Path = page.Path,
                Parent = parent
            };
            node.Children = BuildTree(page.Children, node);
            result.Add(node);
        }
        return result;
    }

    // ── Search ──────────────────────────────────────────────────────────

    /// <summary>
    /// Builds the search index for the current language in the background, so the viewer is
    /// interactive while the pages are read and tokenised. A previous build is cancelled: only
    /// the language that is actually displayed should be indexed.
    /// </summary>
    private void StartIndexBuild()
    {
        _indexCts?.Cancel();           // disposed by the build that owns it, see BuildIndexAsync
        _indexCts = null;
        var cts = new CancellationTokenSource();
        _indexCts = cts;
        _index = null;
        _ = BuildIndexAsync(cts);
    }

    private async Task BuildIndexAsync(CancellationTokenSource cts)
    {
        var ct = cts.Token;
        IsIndexing = true;
        try
        {
            var sources = new List<SearchSource>();
            foreach (var node in Nodes.SelectMany(n => n.DescendantsAndSelf()))
            {
                ct.ThrowIfCancellationRequested();
                var markdown = await ReadPageAsync(node.Path);
                if (!string.IsNullOrWhiteSpace(markdown))
                    sources.Add(new SearchSource(node.Title, node.Path, markdown));
            }

            var index = await Task.Run(() => new WikiSearchIndex(sources), ct);
            ct.ThrowIfCancellationRequested();
            _index = index;

            // A query typed while the index was still building has no results yet.
            if (!string.IsNullOrWhiteSpace(Query))
                QueueSearch(Query);
        }
        catch (OperationCanceledException)
        {
            // Superseded by a newer build (language switch); drop it.
        }
        finally
        {
            if (ReferenceEquals(_indexCts, cts))
                _indexCts = null;
            cts.Dispose();
            IsIndexing = false;
        }
    }

    /// <summary>Debounces a query change, then runs the search off the UI thread.</summary>
    private void QueueSearch(string query)
    {
        _searchCts?.Cancel();          // disposed by the task that owns it, see SearchAsync
        _searchCts = null;

        if (string.IsNullOrWhiteSpace(query))
        {
            // Deliberately NOT clearing Results here. Emptying the query is what navigation does,
            // and navigation is triggered from inside the ListBox's selection commit; clearing the
            // very collection that commit is walking makes the control re-fix its selection
            // re-entrantly and read past the end of the (now shorter) source. The stale rows are
            // never shown — the popup is closed whenever the query is empty — and the next search
            // replaces them: SearchAsync clears and refills.
            return;
        }

        var index = _index;
        if (index is null)
            return;                     // index still building; BuildIndexAsync re-runs this

        var cts = new CancellationTokenSource();
        _searchCts = cts;
        _ = SearchAsync(index, query, cts);
    }

    private async Task SearchAsync(WikiSearchIndex index, string query, CancellationTokenSource cts)
    {
        try
        {
            await Task.Delay(SearchDebounce, cts.Token);
            var hits = await Task.Run(() => index.Search(query), cts.Token);
            cts.Token.ThrowIfCancellationRequested();

            Results.Clear();
            foreach (var hit in hits)
                Results.Add(hit);
        }
        catch (OperationCanceledException)
        {
            // A newer keystroke superseded this query.
        }
        finally
        {
            // Each run disposes its own source. Disposing it from the canceller instead races the
            // cancelled run: a source disposed while `Task.Delay` is still registering its callback
            // throws ObjectDisposedException, which nothing here catches. Clearing the field only
            // if we still own it keeps a later `Cancel()` off a disposed source.
            if (ReferenceEquals(_searchCts, cts))
                _searchCts = null;
            cts.Dispose();
        }
    }

    /// <summary>Clears the query, which collapses the results panel. Bound to Esc and the ✕ button.</summary>
    [RelayCommand]
    private void ClearQuery() => Query = string.Empty;

    /// <summary>
    /// Navigates to a search hit: opens the branches that lead to it, selects it, and closes the
    /// results panel.
    /// </summary>
    public void NavigateTo(SearchHit hit)
    {
        var node = FindNodeByPath(Nodes, hit.Path);
        if (node is null)
            return;

        node.ExpandAncestors();
        SelectedNode = node;
        Query = string.Empty;
    }

    /// <summary>
    /// Handles a hyperlink clicked inside the rendered Markdown.
    /// <para>
    /// Returns <see langword="true"/> when the link is "internal" — i.e. consumed by the app
    /// (a same-language page link that navigates the viewer) or intentionally swallowed because it
    /// cannot be opened safely (unknown scheme, unresolved page path). The caller must set the
    /// event args' <c>Handled</c> flag so the default OS-browser launch is suppressed.
    /// </para>
    /// <para>
    /// Returns <see langword="false"/> for <c>http(s)</c>, <c>mailto:</c> and <c>tel:</c> links so the
    /// default behaviour (open in the system browser / mail client) still applies.
    /// </para>
    /// </summary>
    public bool TryHandleNavigation(string url)
    {
        if (string.IsNullOrWhiteSpace(url) || url.StartsWith('#'))
            return true; // fragment / empty: never reach the OS browser

        if (IsSchemeUrl(url))
        {
            var scheme = url[..url.IndexOf(':')].ToLowerInvariant();
            return scheme is not ("http" or "https" or "mailto" or "tel");
        }

        // No scheme → treat as a same-language page reference. Resolve the target directory
        // path relative to the currently displayed page and select the matching tree node.
        var target = ResolvePagePath(url);
        if (target is null)
        {
            System.Diagnostics.Debug.WriteLine($"[CloudGlyph] Unresolvable link target: {url}");
            return true; // swallow — never throw / open the browser for a bad local link
        }

        var node = FindNodeByPath(Nodes, target);
        if (node is null)
        {
            System.Diagnostics.Debug.WriteLine($"[CloudGlyph] No page matches link target: {target} ({url})");
            return true;
        }

        // Open the branches above the target, or the highlighted item would be hidden inside a
        // collapsed parent and the navigation would look like it did nothing.
        node.ExpandAncestors();
        SelectedNode = node; // two-way TreeView binding highlights it; LoadContentAsync runs
        return true;
    }

    private static bool IsSchemeUrl(string url)
    {
        if (url.Length < 2) return false;
        var c0 = url[0];
        if (!char.IsAsciiLetter(c0)) return false;
        for (var i = 1; i < url.Length; i++)
        {
            var c = url[i];
            if (c == ':') return true;
            if (!(char.IsAsciiLetterOrDigit(c) || c is '+' or '-' or '.')) return false;
        }
        return false;
    }

    /// <summary>
    /// Resolves a relative / root-relative Markdown link destination to a language-root-relative
    /// page directory path. Honors <c>.</c>/<c>..</c> segments and accepts a trailing <c>index.md</c>
    /// or slash. Returns <see langword="null"/> when the target escapes the language root or points
    /// at something that is not a page directory (e.g. a non-index <c>.md</c> file).
    /// </summary>
    private string? ResolvePagePath(string url)
    {
        // Strip any in-page fragment — the viewer navigates to the page itself.
        var frag = url.IndexOf('#');
        if (frag >= 0) url = url[..frag];
        if (string.IsNullOrWhiteSpace(url)) return null;

        // Start from the currently displayed page's directory; a leading '/' resets to the root.
        var stack = (url.StartsWith('/')
            ? null
            : SelectedNode?.Path)
            ?.Split('/', StringSplitOptions.RemoveEmptyEntries)
            .ToList() ?? [];

        foreach (var raw in url.Split('/'))
        {
            switch (raw)
            {
                case "" or ".":
                    continue;
                case "..":
                    if (stack.Count == 0) return null; // escaped above the language root
                    stack.RemoveAt(stack.Count - 1);
                    break;
                default:
                    stack.Add(raw);
                    break;
            }
        }

        // Trailing "index.md" names the directory it lives in; any other .md is not a page dir.
        if (stack.Count > 0 && stack[^1] == "index.md")
            stack.RemoveAt(stack.Count - 1);
        if (stack.Count > 0 && stack[^1].EndsWith(".md", StringComparison.OrdinalIgnoreCase))
            return null;

        return stack.Count == 0 ? "" : string.Join('/', stack);
    }

    /// <summary>Depth-first search for a page node whose <see cref="PageNode.Path"/> equals <paramref name="path"/>.</summary>
    private static PageNode? FindNodeByPath(IEnumerable<PageNode> nodes, string path)
    {
        foreach (var node in nodes)
        {
            if (string.Equals(node.Path, path, StringComparison.OrdinalIgnoreCase))
                return node;
            if (FindNodeByPath(node.Children, path) is { } child)
                return child;
        }
        return null;
    }

    // ── JSON deserialization types ──────────────────────────────────────

    private sealed class TreeRoot
    {
        public List<TreePage> Pages { get; set; } = [];
    }

    private sealed class TreePage
    {
        public string Title { get; set; } = string.Empty;
        public string Path { get; set; } = string.Empty;
        public List<TreePage> Children { get; set; } = [];
    }

    /// <summary>JSON model for each entry in <c>languages_index.json</c>.</summary>
    private sealed record LanguageEntry(string Code, string DisplayName);
}