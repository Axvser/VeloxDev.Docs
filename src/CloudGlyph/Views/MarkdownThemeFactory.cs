using AvalonMarkdown.ViewModels;

namespace CloudGlyph.Views;

/// <summary>
/// Fills a <see cref="MarkdownThemeViewModel"/> with the workbench palette defined in
/// <c>App.axaml</c>, so the rendered document follows the same light/dark tokens as the chrome.
/// The page background is Surface rather than Window: the preview sits inside the content card.
/// </summary>
internal static class MarkdownThemeFactory
{
    public static void Apply(MarkdownThemeViewModel theme, bool dark)
    {
        var p = dark ? Dark : Light;

        (theme.BgR, theme.BgG, theme.BgB) = p.Bg;
        (theme.TextR, theme.TextG, theme.TextB) = p.Text;
        (theme.LinkR, theme.LinkG, theme.LinkB) = p.Link;
        (theme.HeadingR, theme.HeadingG, theme.HeadingB) = p.Heading;
        (theme.CodeR, theme.CodeG, theme.CodeB) = p.Code;
        (theme.BorderR, theme.BorderG, theme.BorderB) = p.Border;
        (theme.BgSecR, theme.BgSecG, theme.BgSecB) = p.BgSec;
        (theme.TextSecR, theme.TextSecG, theme.TextSecB) = p.TextSec;
        (theme.CodeBgR, theme.CodeBgG, theme.CodeBgB) = p.CodeBg;
        (theme.PreBgR, theme.PreBgG, theme.PreBgB) = p.PreBg;
        (theme.TableBgR, theme.TableBgG, theme.TableBgB) = p.TableBg;

        // Diagram and plot containers share one surface; only the plot axis needs its own colour.
        (theme.MermaidBgR, theme.MermaidBgG, theme.MermaidBgB) = p.ContainerBg;
        (theme.PumlBgR, theme.PumlBgG, theme.PumlBgB) = p.ContainerBg;
        (theme.PlotBgR, theme.PlotBgG, theme.PlotBgB) = p.ContainerBg;
        (theme.PlotAxisR, theme.PlotAxisG, theme.PlotAxisB) = p.PlotAxis;

        (theme.ChatBgR, theme.ChatBgG, theme.ChatBgB) = p.ChatBg;
        (theme.ChatAccentR, theme.ChatAccentG, theme.ChatAccentB, theme.ChatAccentA) = p.ChatAccent;
        (theme.ChatGlassR, theme.ChatGlassG, theme.ChatGlassB, theme.ChatGlassA) = p.ChatGlass;

        theme.HljsBackground = p.HljsBackground;
        theme.HljsForeground = p.HljsForeground;
        theme.HljsKeyword = p.HljsKeyword;
        theme.HljsLiteral = p.HljsLiteral;
        theme.HljsName = p.HljsName;
        theme.HljsBuiltIn = p.HljsBuiltIn;
        theme.HljsType = p.HljsType;
        theme.HljsClass = p.HljsClass;
        theme.HljsNumber = p.HljsNumber;
        theme.HljsString = p.HljsString;
        theme.HljsMetaString = p.HljsMetaString;
        theme.HljsTitle = p.HljsTitle;
        theme.HljsTitleClass = p.HljsTitleClass;
        theme.HljsVariable = p.HljsVariable;
        theme.HljsComment = p.HljsComment;
        theme.HljsQuote = p.HljsQuote;
        theme.HljsAttr = p.HljsAttr;
        theme.HljsAttribute = p.HljsAttribute;
        theme.HljsMeta = p.HljsMeta;
        theme.HljsTag = p.HljsTag;
        theme.HljsSelectorAttr = p.HljsSelectorAttr;
        theme.HljsSelectorClass = p.HljsSelectorClass;
        theme.HljsSelectorId = p.HljsSelectorId;
        theme.HljsSelectorPseudo = p.HljsSelectorPseudo;
        theme.HljsSelectorTag = p.HljsSelectorTag;
        theme.HljsBullet = p.HljsBullet;
        theme.HljsSection = p.HljsSection;
        theme.HljsLink = p.HljsLink;
        theme.HljsRegexp = p.HljsRegexp;
        theme.HljsTemplateTag = p.HljsTemplateTag;
        theme.HljsDoctag = p.HljsDoctag;
        theme.HljsAdditionBg = p.HljsAdditionBg;
        theme.HljsAdditionColor = p.HljsAdditionColor;
        theme.HljsDeletionBg = p.HljsDeletionBg;
        theme.HljsDeletionColor = p.HljsDeletionColor;

        theme.CodeFontSize = 12.5;
        theme.BorderRadius = 8;
        theme.HeadingMarginTop = 20;
        theme.HeadingMarginBottom = 10;

        theme.MermaidContainerPadding = 12;
        theme.MermaidContainerMargin = 12;
        theme.MermaidBorderRadius = 8;
        theme.PumlContainerPadding = 12;
        theme.PumlContainerMargin = 12;
        theme.PumlBorderRadius = 8;
        theme.PumlDarkInvert = dark ? 1 : 0;
        theme.PlotContainerPadding = 12;
        theme.PlotContainerMargin = 12;
        theme.PlotBorderRadius = 8;
        theme.ChatContainerPadding = 12;
        theme.ChatContainerMargin = 12;
        theme.ChatBorderRadius = 12;
        theme.ChatGlassBlur = 18;
    }

    private readonly record struct Rgb(int R, int G, int B);

    private sealed class Palette
    {
        public Rgb Bg;
        public Rgb Text;
        public Rgb Link;
        public Rgb Heading;
        public Rgb Code;
        public Rgb Border;
        public Rgb BgSec;
        public Rgb TextSec;
        public Rgb CodeBg;
        public Rgb PreBg;
        public Rgb TableBg;
        public Rgb ContainerBg;
        public Rgb PlotAxis;
        public Rgb ChatBg;
        public (int R, int G, int B, int A) ChatAccent;
        public (int R, int G, int B, int A) ChatGlass;

        public string HljsBackground = "";
        public string HljsForeground = "";
        public string HljsKeyword = "";
        public string HljsLiteral = "";
        public string HljsName = "";
        public string HljsBuiltIn = "";
        public string HljsType = "";
        public string HljsClass = "";
        public string HljsNumber = "";
        public string HljsString = "";
        public string HljsMetaString = "";
        public string HljsTitle = "";
        public string HljsTitleClass = "";
        public string HljsVariable = "";
        public string HljsComment = "";
        public string HljsQuote = "";
        public string HljsAttr = "";
        public string HljsAttribute = "";
        public string HljsMeta = "";
        public string HljsTag = "";
        public string HljsSelectorAttr = "";
        public string HljsSelectorClass = "";
        public string HljsSelectorId = "";
        public string HljsSelectorPseudo = "";
        public string HljsSelectorTag = "";
        public string HljsBullet = "";
        public string HljsSection = "";
        public string HljsLink = "";
        public string HljsRegexp = "";
        public string HljsTemplateTag = "";
        public string HljsDoctag = "";
        public string HljsAdditionBg = "";
        public string HljsAdditionColor = "";
        public string HljsDeletionBg = "";
        public string HljsDeletionColor = "";
    }

    private static readonly Palette Dark = new()
    {
        Bg = new(0x25, 0x25, 0x26),          // Surface
        Text = new(0xE7, 0xE7, 0xE7),
        Link = new(0x00, 0x78, 0xD4),        // Accent
        Heading = new(0xE7, 0xE7, 0xE7),
        Code = new(0xCE, 0x91, 0x78),
        Border = new(0x33, 0x33, 0x33),
        BgSec = new(0x2D, 0x2D, 0x2D),       // Raised
        TextSec = new(0xA0, 0xA0, 0xA0),     // Muted
        CodeBg = new(0x2D, 0x2D, 0x2D),
        PreBg = new(0x1E, 0x1E, 0x1E),
        TableBg = new(0x2D, 0x2D, 0x2D),
        ContainerBg = new(0x2D, 0x2D, 0x2D),
        PlotAxis = new(0xA0, 0xA0, 0xA0),
        ChatBg = new(0x2D, 0x2D, 0x2D),
        ChatAccent = (0x00, 0x78, 0xD4, 0xFF),
        ChatGlass = (0x00, 0x78, 0xD4, 0x30),

        HljsBackground = "#1E1E1E",
        HljsForeground = "#D4D4D4",
        HljsKeyword = "#569CD6",
        HljsLiteral = "#569CD6",
        HljsName = "#E7E7E7",
        HljsBuiltIn = "#4EC9B0",
        HljsType = "#4EC9B0",
        HljsClass = "#4EC9B0",
        HljsNumber = "#B5CEA8",
        HljsString = "#CE9178",
        HljsMetaString = "#CE9178",
        HljsTitle = "#DCDCAA",
        HljsTitleClass = "#4EC9B0",
        HljsVariable = "#9CDCFE",
        HljsComment = "#6A9955",
        HljsQuote = "#6A9955",
        HljsAttr = "#9CDCFE",
        HljsAttribute = "#9CDCFE",
        HljsMeta = "#569CD6",
        HljsTag = "#569CD6",
        HljsSelectorAttr = "#D7BA7D",
        HljsSelectorClass = "#D7BA7D",
        HljsSelectorId = "#D7BA7D",
        HljsSelectorPseudo = "#D7BA7D",
        HljsSelectorTag = "#569CD6",
        HljsBullet = "#6796E6",
        HljsSection = "#569CD6",
        HljsLink = "#4FC1FF",
        HljsRegexp = "#D16969",
        HljsTemplateTag = "#569CD6",
        HljsDoctag = "#569CD6",
        HljsAdditionBg = "#204A2B",
        HljsAdditionColor = "#B5CEA8",
        HljsDeletionBg = "#4B1818",
        HljsDeletionColor = "#F48771",
    };

    private static readonly Palette Light = new()
    {
        Bg = new(0xF3, 0xF3, 0xF3),          // Surface
        Text = new(0x33, 0x33, 0x33),
        Link = new(0x00, 0x78, 0xD4),        // Accent
        Heading = new(0x33, 0x33, 0x33),
        Code = new(0xA3, 0x15, 0x15),
        Border = new(0xCE, 0xCE, 0xCE),
        BgSec = new(0xDD, 0xDD, 0xDD),       // Raised
        TextSec = new(0x6F, 0x6F, 0x6F),     // Muted
        CodeBg = new(0xE8, 0xE8, 0xE8),
        PreBg = new(0xFF, 0xFF, 0xFF),
        TableBg = new(0xDD, 0xDD, 0xDD),
        ContainerBg = new(0xFF, 0xFF, 0xFF),
        PlotAxis = new(0x6F, 0x6F, 0x6F),
        ChatBg = new(0xE8, 0xE8, 0xE8),
        ChatAccent = (0x00, 0x78, 0xD4, 0xFF),
        ChatGlass = (0x00, 0x78, 0xD4, 0x28),

        HljsBackground = "#FFFFFF",
        HljsForeground = "#333333",
        HljsKeyword = "#0000FF",
        HljsLiteral = "#0000FF",
        HljsName = "#001080",
        HljsBuiltIn = "#267F99",
        HljsType = "#267F99",
        HljsClass = "#267F99",
        HljsNumber = "#098658",
        HljsString = "#A31515",
        HljsMetaString = "#A31515",
        HljsTitle = "#795E26",
        HljsTitleClass = "#267F99",
        HljsVariable = "#001080",
        HljsComment = "#008000",
        HljsQuote = "#008000",
        HljsAttr = "#E50000",
        HljsAttribute = "#E50000",
        HljsMeta = "#0000FF",
        HljsTag = "#800000",
        HljsSelectorAttr = "#800000",
        HljsSelectorClass = "#267F99",
        HljsSelectorId = "#267F99",
        HljsSelectorPseudo = "#0000FF",
        HljsSelectorTag = "#800000",
        HljsBullet = "#0000FF",
        HljsSection = "#800000",
        HljsLink = "#0000FF",
        HljsRegexp = "#811F3F",
        HljsTemplateTag = "#800000",
        HljsDoctag = "#800000",
        HljsAdditionBg = "#E6FFEC",
        HljsAdditionColor = "#22863A",
        HljsDeletionBg = "#FFEBE9",
        HljsDeletionColor = "#CB2431",
    };
}
