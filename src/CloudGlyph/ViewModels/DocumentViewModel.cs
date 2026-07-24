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

    private bool _markdownViewReady;

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
    private string _title = "VeloxDev Docs";

    [ObservableProperty]
    private bool _isLoading;

    public DocumentViewModel()
    {
        _ = InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        await LoadLanguagesAsync();
        await LoadTreeAsync();
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
    public void MarkdownViewReady()
    {
        _markdownViewReady = true;
        if (SelectedNode is not null)
            _ = LoadContentAsync(SelectedNode);
    }

    /// <summary>Called by the view to render the current content when ready.</summary>
    public Func<string, Task>? RenderMarkdownAsync { get; set; }

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
        _markdownViewReady = false;
        Content = string.Empty;
        SelectedNode = null;
        await LoadTreeAsync();
        // Restore ready state: the MarkdownView WebView was not destroyed,
        // only the tree/content was reloaded.
        _markdownViewReady = true;
        // LoadTreeAsync auto-selected the first node, but OnSelectedNodeChanged
        // fired while _markdownViewReady was still false and returned early.
        // Re-trigger content loading for the now-selected node.
        if (SelectedNode is not null)
            await LoadContentAsync(SelectedNode);
    }

    private async Task LoadContentAsync(PageNode node)
    {
        if (!_markdownViewReady || RenderMarkdownAsync is null)
            return;

        IsLoading = true;
        try
        {
            var code = string.IsNullOrWhiteSpace(Language) ? DefaultLanguage : Language.ToLowerInvariant();
            var mdPath = $"{node.Path}/index.md";
            var uri = new Uri($"avares://CloudGlyph/Assets/Docs/content/{code}/{mdPath.Replace('\\', '/')}");

            string markdown;
            try
            {
                using var stream = AssetLoader.Open(uri);
                using var reader = new StreamReader(stream, Encoding.UTF8);
                markdown = await reader.ReadToEndAsync();
            }
            catch (FileNotFoundException)
            {
                markdown = $"# {node.Title}\n\n*Content not available in this language.*";
            }

            Content = markdown;
            await RenderMarkdownAsync(markdown);
        }
        catch (Exception ex)
        {
            Content = $"# Error\n\nFailed to load content: {ex.Message}";
            await RenderMarkdownAsync(Content);
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