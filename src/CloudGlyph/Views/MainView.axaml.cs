using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Platform;
using Avalonia.Styling;
using Avalonia.Threading;
using Avalonia.VisualTree;
using AvalonMarkdown.ViewModels;
using AvalonMarkdown.Views;
using CloudGlyph.ViewModels;

namespace CloudGlyph.Views
{
    public partial class MainView : UserControl
    {
        /// <summary>Console-bridge token the preview page sends when Ctrl+K is pressed inside it.</summary>
        private const string SearchHotkeyToken = "CG_FOCUS_SEARCH";

        /// <summary>
        /// Preview page setup: no follow-the-newest-content scrolling, plus a Ctrl+K listener that
        /// reports through the console bridge. Re-applied whenever the preview becomes ready.
        /// </summary>
        private const string PreviewSetupScript = """
            (function () {
                setPreviewConfig({ autoScrollOnUpdate: false });
                if (window.__cgSearchHotkey) return;
                window.__cgSearchHotkey = true;
                document.addEventListener('keydown', function (e) {
                    if (e.ctrlKey && !e.altKey && !e.shiftKey && e.key && e.key.toLowerCase() === 'k') {
                        e.preventDefault();
                        console.log('CG_FOCUS_SEARCH');
                    }
                }, true);
            })()
            """;

        private readonly MarkdownThemeViewModel _markdownTheme = new();
        private MainViewModel? _viewModel;
        private CancellationTokenSource? _scrollResetCts;
        private bool? _darkMode;

        public MainView()
        {
            InitializeComponent();

            // Ctrl+K focuses the search box, as in an editor's quick-open. Tunnelling, so it works
            // wherever focus sits inside the view (note: key events go to the WebView, not here,
            // while the rendered page itself has focus — there the box is reachable by click).
            AddHandler(KeyDownEvent, OnPreviewKeyDown, RoutingStrategies.Tunnel);

            // Route links clicked inside the rendered Markdown: same-language page links navigate
            // the tree; web/mail links keep the library's default (open in the OS browser).
            MarkdownPreview.LinkClicked += (_, e) =>
            {
                if (DataContext is not MainViewModel vm) return;
                if (vm.Document.TryHandleNavigation(e.Url))
                {
                    e.Handled = true;
                    _ = ResetScrollTopAsync();
                }
            };

            // The rendered page is HTML inside a WebView, so it cannot inherit the app's
            // ThemeDictionaries. Register the theme view model and keep it in step with the
            // chrome from ApplyTheme/ApplyMarkdownTheme below.
            _markdownTheme.RegisterRenderer(MarkdownPreview);
            _markdownTheme.StartAutoApply();
            ApplyMarkdownTheme(Application.Current?.ActualThemeVariant == ThemeVariant.Dark);

            // The renderer runs in a native WebView; a shortcut pressed there never reaches
            // Avalonia. Its listener posts a token back through the console bridge instead.
            MarkdownPreview.ConsoleMessage += OnMarkdownConsoleMessage;
            MarkdownPreview.OnReady += (_, _) => _ = PrepareMarkdownPreviewAsync();

            Loaded += (s, e) =>
            {
                AttachViewModel(DataContext as MainViewModel);

                var settings = this.GetPlatformSettings();

                if (settings?.GetColorValues() is PlatformColorValues colors)
                {
                    ApplyTheme(colors);
                }

                settings?.ColorValuesChanged += (sender, values) =>
                {
                    if (settings.GetColorValues() is PlatformColorValues colors)
                    {
                        ApplyTheme(colors);
                    }
                };

                if (Application.Current is { } app)
                    app.ActualThemeVariantChanged += OnActualThemeVariantChanged;

                // The constructor may have tried before the WebView existed; retry once it is ready.
                _ = PrepareMarkdownPreviewAsync();
            };
        }

        /// <summary>Ctrl+K moves focus into the search box and selects what is already there.</summary>
        private void OnPreviewKeyDown(object? sender, KeyEventArgs e)
        {
            if (e.Key != Key.K || !e.KeyModifiers.HasFlag(KeyModifiers.Control))
                return;

            FocusSearchBox();
            e.Handled = true;
        }

        // ── Navigation pane splitter ─────────────────────────────────────

        private bool _draggingPane;
        private double _paneGrabOffset;

        private void OnPaneSplitterPointerPressed(object? sender, PointerPressedEventArgs e)
        {
            if (!e.GetCurrentPoint(this).Properties.IsLeftButtonPressed)
                return;

            _draggingPane = true;
            _paneGrabOffset = e.GetPosition(WorkspaceGrid).X - WorkspaceGrid.ColumnDefinitions[0].ActualWidth;
            e.Pointer.Capture(PaneSplitter);
            e.Handled = true;
        }

        /// <summary>
        /// Sets the pane width from the pointer's absolute position on every move, so the result
        /// depends on where the pointer is — not on the rounded width the previous move produced.
        /// </summary>
        private void OnPaneSplitterPointerMoved(object? sender, PointerEventArgs e)
        {
            if (!_draggingPane)
                return;

            var columns = WorkspaceGrid.ColumnDefinitions;
            var width = e.GetPosition(WorkspaceGrid).X - _paneGrabOffset;
            var max = Math.Max(columns[0].MinWidth,
                Math.Min(columns[0].MaxWidth,
                    WorkspaceGrid.Bounds.Width - PaneSplitter.Bounds.Width - columns[2].MinWidth));

            columns[0].Width = new GridLength(Math.Clamp(width, columns[0].MinWidth, max));
            e.Handled = true;
        }

        private void OnPaneSplitterPointerReleased(object? sender, PointerReleasedEventArgs e)
        {
            if (!_draggingPane)
                return;

            _draggingPane = false;
            e.Pointer.Capture(null);
            e.Handled = true;
        }

        private void OnPaneSplitterPointerCaptureLost(object? sender, PointerCaptureLostEventArgs e)
            => _draggingPane = false;

        /// <summary>Moves keyboard focus into the search box and selects its current text.</summary>
        private void FocusSearchBox()
        {
            SearchBox.Focus();
            SearchBox.SelectAll();

            // While the native WebView has been clicked it owns the OS keyboard focus; moving
            // Avalonia's logical focus is not enough, so hand the window's native focus back too.
            if (OperatingSystem.IsWindows() &&
                TopLevel.GetTopLevel(this)?.TryGetPlatformHandle()?.Handle is { } window)
            {
                SetNativeFocus(window);
            }
        }

        [System.Runtime.InteropServices.DllImport("user32.dll", EntryPoint = "SetFocus")]
        private static extern IntPtr SetNativeFocus(IntPtr hWnd);

        /// <summary>
        /// Ctrl+K pressed inside the rendered page arrives here as a console line, because the
        /// native WebView owns the keyboard while the document has focus. Other lines are real
        /// console output and are ignored.
        /// </summary>
        private void OnMarkdownConsoleMessage(object? sender, MarkdownConsoleMessageEventArgs e)
        {
            if (!string.Equals(e.Message?.Trim(), SearchHotkeyToken, StringComparison.Ordinal))
                return;

            if (Dispatcher.UIThread.CheckAccess())
                FocusSearchBox();
            else
                Dispatcher.UIThread.Post(FocusSearchBox);
        }

        private void AttachViewModel(MainViewModel? vm)
        {
            if (_viewModel == vm) return;
            if (_viewModel is not null)
                _viewModel.Document.PropertyChanged -= OnDocumentPropertyChanged;
            _viewModel = vm;
            if (_viewModel is not null)
                _viewModel.Document.PropertyChanged += OnDocumentPropertyChanged;
        }

        private void OnDocumentPropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            // A new page was selected (left tree or an in-content link): start the page at the top.
            if (e.PropertyName == nameof(DocumentViewModel.SelectedNode))
                _ = ResetScrollTopAsync();
        }

        /// <summary>
        /// Best-effort scroll-to-top after the document is replaced. Content rendering is async after
        /// <c>Text</c> changes, so retry for a short window and swallow any "not ready" errors.
        /// </summary>
        private async Task ResetScrollTopAsync()
        {
            _scrollResetCts?.Cancel();
            var cts = new CancellationTokenSource();
            _scrollResetCts = cts;
            try
            {
                for (var i = 0; i < 6; i++)
                {
                    await Task.Delay(80, cts.Token);
                    await MarkdownPreview.ScrollToProgressAsync(0);
                }
            }
            catch (OperationCanceledException)
            {
                // superseded by a newer navigation
            }
            catch
            {
                // preview not ready yet / control detached — nothing to reset
            }
        }

        /// <summary>
        /// Follows the OS: sets the app's theme variant (so Fluent controls and every
        /// <c>DynamicResource</c> palette token switch together) and then mirrors the same
        /// choice into the rendered Markdown.
        /// </summary>
        private void ApplyTheme(PlatformColorValues colors)
        {
            // Platform color notifications are not guaranteed to land on the UI thread.
            if (!Dispatcher.UIThread.CheckAccess())
            {
                Dispatcher.UIThread.Post(() => ApplyTheme(colors));
                return;
            }

            var dark = (ThemeVariant?)colors?.ThemeVariant == ThemeVariant.Dark;
            var variant = dark ? ThemeVariant.Dark : ThemeVariant.Light;

            if (Application.Current is { } app && app.RequestedThemeVariant != variant)
                app.RequestedThemeVariant = variant;

            ApplyMarkdownTheme(dark);
        }

        private void OnActualThemeVariantChanged(object? sender, EventArgs e)
        {
            ApplyMarkdownTheme(Application.Current?.ActualThemeVariant == ThemeVariant.Dark);
        }

        /// <summary>Repaints the Markdown palette, but only when the variant actually changed.</summary>
        private void ApplyMarkdownTheme(bool dark)
        {
            if (_darkMode == dark) return;
            _darkMode = dark;

            _markdownTheme.StopAutoApply();
            MarkdownThemeFactory.Apply(_markdownTheme, dark);
            _markdownTheme.StartAutoApply();

            // StartAutoApply only guarantees future changes; paint the initial stylesheet once.
            _ = ApplyMarkdownCssAsync();
        }

        private async Task ApplyMarkdownCssAsync()
        {
            try
            {
                await MarkdownPreview.ApplyCustomCssAsync(_markdownTheme.GenerateCss());
            }
            catch
            {
                // Preview not ready yet — the next render/theme change applies the stylesheet.
            }
        }

        /// <summary>
        /// Waits briefly for the preview page, then installs its setup script (auto-scroll off,
        /// Ctrl+K listener) and the theme stylesheet. A wiki page opens at the top and stays where
        /// the reader leaves it — only the explicit scroll reset on navigation may move it.
        /// </summary>
        private async Task PrepareMarkdownPreviewAsync()
        {
            for (var i = 0; i < 20 && !MarkdownPreview.IsReady; i++)
                await Task.Delay(100);

            try
            {
                await MarkdownPreview.ApplyConfigAsync(PreviewSetupScript);
            }
            catch
            {
                // The page keeps its defaults (follow content, Ctrl+K only in the chrome).
            }

            await ApplyMarkdownCssAsync();
        }
    }
}
