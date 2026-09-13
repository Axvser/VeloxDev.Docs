using System.Collections.Generic;
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;

namespace CloudGlyph.Models;

/// <summary>
/// One page in the navigation tree, mirroring an entry of the generated <c>tree.json</c>.
/// <para>
/// <see cref="IsExpanded"/> lives on the model rather than on the <c>TreeViewItem</c> so the
/// tree's expansion is view-model state: the document view model can open the branches that
/// lead to a page it navigates to (a link click, a search result) without reaching into the
/// view. The view binds each <c>TreeViewItem.IsExpanded</c> to it two-way.
/// </para>
/// </summary>
public partial class PageNode : ObservableObject
{
    [ObservableProperty]
    private string _title = string.Empty;

    [ObservableProperty]
    private string _path = string.Empty;

    [ObservableProperty]
    private bool _isExpanded;

    public ObservableCollection<PageNode> Children { get; set; } = [];

    /// <summary>The page this one is nested under, or <see langword="null"/> for a top-level dimension.</summary>
    public PageNode? Parent { get; set; }

    /// <summary>True when this node owns no sub-pages, so a tree item can show it as a leaf.</summary>
    public bool IsLeaf => Children.Count == 0;

    /// <summary>Opens every ancestor of this node so the node is visible in the tree.</summary>
    public void ExpandAncestors()
    {
        for (var ancestor = Parent; ancestor is not null; ancestor = ancestor.Parent)
            ancestor.IsExpanded = true;
    }

    /// <summary>Every node of this subtree, this node first (depth-first).</summary>
    public IEnumerable<PageNode> DescendantsAndSelf()
    {
        yield return this;
        foreach (var child in Children)
            foreach (var node in child.DescendantsAndSelf())
                yield return node;
    }

    public override string ToString() => Title;
}
