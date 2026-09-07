using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Avalonia.Platform;
using CommunityToolkit.Mvvm.ComponentModel;
using CloudGlyph.Models;

namespace CloudGlyph.ViewModels;

public sealed record LanguageOption(string Code, string DisplayName);

public partial class DocumentViewModel : ObservableObject
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public const string DefaultLanguage = "en";

    private List<LanguageOption> _loadedLanguages = [];

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

    public DocumentViewModel()
    {
        _ = InitializeAsync();
    }

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
    }

    private async Task ReloadAsync()
    {
        Content = string.Empty;
        SelectedNode = null;
        await LoadTreeAsync();
    }

    private async Task LoadContentAsync(PageNode node)
    {
        IsLoading = true;
        try
        {
            var code = string.IsNullOrWhiteSpace(Language) ? DefaultLanguage : Language.ToLowerInvariant();
            var mdPath = $"{node.Path}/index.md";
            var uri = new Uri($"avares://CloudGlyph/Assets/Docs/content/{code}/{mdPath.Replace('\\', '/')}");

            string? markdown;
            try
            {
                using var stream = AssetLoader.Open(uri);
                using var reader = new StreamReader(stream, Encoding.UTF8);
                markdown = await reader.ReadToEndAsync();
            }
            catch (FileNotFoundException)
            {
                markdown = null;
            }

            // If the page has no real content and has children,
            // auto-redirect to the first child page.
            if (string.IsNullOrWhiteSpace(markdown) && node.Children.Count > 0)
            {
                SelectedNode = node.Children[0];
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

    private static ObservableCollection<PageNode> BuildTree(List<TreePage>? pages)
    {
        var result = new ObservableCollection<PageNode>();
        if (pages is null) return result;

        foreach (var page in pages)
        {
            var node = new PageNode
            {
                Title = page.Title,
                Path = page.Path,
                Children = BuildTree(page.Children)
            };
            result.Add(node);
        }
        return result;
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