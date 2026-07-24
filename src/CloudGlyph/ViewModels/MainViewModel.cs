using CommunityToolkit.Mvvm.ComponentModel;

namespace CloudGlyph.ViewModels;

public partial class MainViewModel : ObservableObject
{
    [ObservableProperty]
    private DocumentViewModel _document = new();
}
