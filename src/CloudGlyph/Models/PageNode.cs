using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;

namespace CloudGlyph.Models;

public partial class PageNode : ObservableObject
{
    [ObservableProperty]
    private string _title = string.Empty;

    [ObservableProperty]
    private string _path = string.Empty;

    public ObservableCollection<PageNode> Children { get; set; } = [];

    public override string ToString() => Title;
}
