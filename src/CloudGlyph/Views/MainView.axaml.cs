using Avalonia.Controls;
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
        public MainView()
        {
            InitializeComponent();

            InitializeTheme();

            MarkdownPreview.OnReady += async (_, _) =>
            {
                if (DataContext is MainViewModel vm)
                {
                    vm.Document.RenderMarkdownAsync = async md =>
                    {
                        await MarkdownPreview.RenderMarkdownAsync(md);
                    };
                    vm.Document.MarkdownViewReady();
                }
            };

            Loaded += (s, e) =>
            {
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
