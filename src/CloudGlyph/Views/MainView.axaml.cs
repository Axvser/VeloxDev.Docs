using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Platform;
using Avalonia.Styling;
using Avalonia.VisualTree;
using CloudGlyph.ViewModels;
using VeloxDev.DynamicTheme;

namespace CloudGlyph.Views
{
    [ThemeConfig<ObjectConverter, Dark, Light>(nameof(Background), ["#1e1e1e"], ["#ffffff"])]
    public partial class MainView : UserControl
    {
        private MainViewModel? _viewModel;
        private CancellationTokenSource? _scrollResetCts;

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

            InitializeTheme();

            Loaded += (s, e) =>
            {
                AttachViewModel(DataContext as MainViewModel);

                var settings = this.GetPlatformSettings();

                if (settings?.GetColorValues() is PlatformColorValues colors)
                {
                    UpdateTheme(colors);
                }

                settings?.ColorValuesChanged += (sender, values) =>
                {
                    if (settings.GetColorValues() is PlatformColorValues colors)
                    {
                        UpdateTheme(colors);
                    }
                };
            };
        }

        /// <summary>Ctrl+K moves focus into the search box and selects what is already there.</summary>
        private void OnPreviewKeyDown(object? sender, KeyEventArgs e)
        {
            if (e.Key != Key.K || !e.KeyModifiers.HasFlag(KeyModifiers.Control))
                return;

            SearchBox.Focus();
            SearchBox.SelectAll();
            e.Handled = true;
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

        private static void UpdateTheme(PlatformColorValues colors)
        {
            if ((ThemeVariant?)colors?.ThemeVariant == ThemeVariant.Dark)
            {
                ThemeManager.Jump<Dark>();
            }
            else
            {
                ThemeManager.Jump<Light>();
            }
        }
    }
}
