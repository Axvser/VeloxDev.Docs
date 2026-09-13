using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace CloudGlyph.Services;

/// <summary>One page as the index sees it: the text that was indexed, plus where it came from.</summary>
public sealed record SearchSource(string Title, string Path, string Body);

/// <summary>A ranked match, ready for the view to display and navigate to.</summary>
public sealed record SearchHit(string Title, string Path, string Snippet, int Score);

/// <summary>
/// A small in-memory inverted index over the pages of one language tree.
/// <para>
/// It is deliberately dependency-free: it takes already-loaded page text (see
/// <see cref="SearchSource"/>) so building and querying can be exercised without a view or an
/// asset loader, and so the caller decides where the text comes from.
/// </para>
/// <para>
/// <b>Tokenisation.</b> A run of letters and digits becomes one lower-cased word; a run of CJK
/// characters becomes both its single characters and its adjacent pairs. The pairs are what make
/// a Chinese query precise — <c>编译</c> matches the pair <c>编译</c> rather than every page that
/// happens to contain <c>编</c> and <c>译</c> anywhere — while the single characters still let a
/// one-character query match at all.
/// </para>
/// <para>
/// <b>Matching.</b> Every query token must match (AND), and a token matches any indexed word it
/// is a prefix of, which is what makes the index usable while the reader is still typing.
/// </para>
/// </summary>
public sealed class WikiSearchIndex
{
    private const int MaxPrefixExpansion = 128;  // bound the work a very short query can cause
    private const int MaxBodyHitsPerToken = 5;   // a term repeated 40 times is not 40x more relevant
    private const int TitleWeight = 12;
    private const int PhraseInTitleBonus = 40;
    private const int PhraseInBodyBonus = 8;
    private const int SnippetRadius = 70;

    private readonly List<SearchSource> _docs;
    private readonly Dictionary<string, List<int>> _postings;
    private readonly string[] _keys;             // sorted distinct tokens, for prefix scans
    private readonly string[] _searchable;       // cleaned body per doc, original casing

    public WikiSearchIndex(IEnumerable<SearchSource> sources)
    {
        _docs = [.. sources];
        _postings = new Dictionary<string, List<int>>(StringComparer.Ordinal);
        _searchable = new string[_docs.Count];

        var tokens = new List<string>();
        for (var i = 0; i < _docs.Count; i++)
        {
            var body = Clean(_docs[i].Body);
            _searchable[i] = body;

            tokens.Clear();
            Tokenize(_docs[i].Title, tokens);
            Tokenize(body, tokens);
            foreach (var token in tokens.Distinct(StringComparer.Ordinal))
            {
                if (!_postings.TryGetValue(token, out var ids))
                    _postings[token] = ids = [];
                if (ids.Count == 0 || ids[^1] != i)
                    ids.Add(i);      // docs are visited in order, so appends stay sorted
            }
        }

        _keys = [.. _postings.Keys];
        Array.Sort(_keys, StringComparer.Ordinal);
    }

    /// <summary>Number of indexed pages.</summary>
    public int Count => _docs.Count;

    /// <summary>
    /// Ranks the pages matching every token of <paramref name="query"/>, best first.
    /// An empty query returns nothing; so does a query whose tokens are all unknown.
    /// </summary>
    public IReadOnlyList<SearchHit> Search(string? query, int maxResults = 50)
    {
        if (string.IsNullOrWhiteSpace(query) || _docs.Count == 0)
            return [];

        var tokens = new List<string>();
        Tokenize(query, tokens);
        var distinct = tokens.Distinct(StringComparer.Ordinal).ToArray();
        if (distinct.Length == 0)
            return [];

        // Intersect the candidates for every token: a page must match all of them.
        HashSet<int>? candidates = null;
        foreach (var token in distinct)
        {
            var hits = CandidatesFor(token);
            if (hits.Count == 0)
                return [];
            if (candidates is null)
                candidates = [.. hits];
            else
                candidates.IntersectWith(hits);
            if (candidates.Count == 0)
                return [];
        }

        var phrase = string.Join(' ', distinct);
        var scored = new List<SearchHit>();
        foreach (var id in candidates!)
        {
            var doc = _docs[id];
            var title = doc.Title;
            var body = _searchable[id];
            var score = 0;

            foreach (var token in distinct)
            {
                if (title.Contains(token, StringComparison.OrdinalIgnoreCase))
                    score += TitleWeight;
                score += Math.Min(CountOccurrences(body, token), MaxBodyHitsPerToken);
            }

            if (title.Contains(phrase, StringComparison.OrdinalIgnoreCase))
                score += PhraseInTitleBonus;
            else if (body.Contains(phrase, StringComparison.OrdinalIgnoreCase))
                score += PhraseInBodyBonus;

            scored.Add(new SearchHit(title, doc.Path, Snippet(body, distinct), score));
        }

        return [.. scored
            .OrderByDescending(h => h.Score)
            .ThenBy(h => h.Title, StringComparer.OrdinalIgnoreCase)
            .ThenBy(h => h.Path, StringComparer.Ordinal)
            .Take(maxResults)];
    }

    /// <summary>Document ids for a token — the token itself plus every indexed word it prefixes.</summary>
    private List<int> CandidatesFor(string token)
    {
        var result = new List<int>();
        if (_postings.TryGetValue(token, out var exact))
            result.AddRange(exact);

        // Prefix scan over the sorted key array, so "interp" finds "interpolator".
        var start = Array.BinarySearch(_keys, token, StringComparer.Ordinal);
        if (start < 0) start = ~start;
        var expanded = 0;
        for (var i = start; i < _keys.Length && expanded < MaxPrefixExpansion; i++)
        {
            if (!_keys[i].StartsWith(token, StringComparison.Ordinal))
                break;
            if (_keys[i] == token)
                continue;                 // already added above
            result.AddRange(_postings[_keys[i]]);
            expanded++;
        }

        result.Sort();
        // dedupe in place
        var write = 0;
        for (var read = 0; read < result.Count; read++)
        {
            if (write == 0 || result[read] != result[write - 1])
                result[write++] = result[read];
        }
        result.RemoveRange(write, result.Count - write);
        return result;
    }

    private static int CountOccurrences(string haystack, string needle)
    {
        var count = 0;
        var index = 0;
        while ((index = haystack.IndexOf(needle, index, StringComparison.OrdinalIgnoreCase)) >= 0)
        {
            count++;
            index += needle.Length;
        }
        return count;
    }

    /// <summary>A one-line window of the body around the first matched term.</summary>
    private static string Snippet(string body, IReadOnlyList<string> tokens)
    {
        var at = -1;
        foreach (var token in tokens)
        {
            at = body.IndexOf(token, StringComparison.OrdinalIgnoreCase);
            if (at >= 0)
                break;
        }

        if (at < 0)
            return Extract(body, 0, SnippetRadius * 2).Trim();

        var start = Math.Max(0, at - SnippetRadius);
        var end = Math.Min(body.Length, at + SnippetRadius);
        var text = Extract(body, start, end - start).Trim();
        return (start > 0 ? "… " : "") + text + (end < body.Length ? " …" : "");
    }

    private static string Extract(string text, int start, int length) =>
        text.Substring(start, Math.Min(length, text.Length - start))
            .Replace('\n', ' ')
            .Replace('\r', ' ');

    /// <summary>
    /// Keeps the text a reader would actually see: style blocks, comments and HTML tags are
    /// dropped (a page's CSS is not content), while fenced code is kept because identifiers
    /// inside it are exactly what a reader searches for.
    /// </summary>
    private static string Clean(string markdown)
    {
        if (string.IsNullOrEmpty(markdown))
            return string.Empty;

        var text = StripBetween(markdown, "<style", "</style>");
        text = StripComments(text);
        return StripTags(text);
    }

    private static string StripBetween(string text, string open, string close)
    {
        var result = new StringBuilder(text.Length);
        var index = 0;
        while (index < text.Length)
        {
            var start = text.IndexOf(open, index, StringComparison.OrdinalIgnoreCase);
            if (start < 0)
                break;
            result.Append(text, index, start - index);
            var end = text.IndexOf(close, start, StringComparison.OrdinalIgnoreCase);
            if (end < 0)
                return result.ToString();
            index = end + close.Length;
        }
        result.Append(text, index, text.Length - index);
        return result.ToString();
    }

    private static string StripComments(string text)
    {
        var result = new StringBuilder(text.Length);
        var index = 0;
        while (index < text.Length)
        {
            var start = text.IndexOf("<!--", index, StringComparison.Ordinal);
            if (start < 0)
                break;
            result.Append(text, index, start - index);
            var end = text.IndexOf("-->", start, StringComparison.Ordinal);
            if (end < 0)
                return result.ToString();
            index = end + 3;
        }
        result.Append(text, index, text.Length - index);
        return result.ToString();
    }

    private static string StripTags(string text)
    {
        var result = new StringBuilder(text.Length);
        var inTag = false;
        foreach (var c in text)
        {
            if (c == '<') inTag = true;
            else if (c == '>') { inTag = false; result.Append(' '); }
            else if (!inTag) result.Append(c);
        }
        return result.ToString();
    }

    /// <summary>
    /// Splits <paramref name="text"/> into index terms: lower-cased word runs, and CJK
    /// characters as both single characters and adjacent pairs.
    /// </summary>
    public static void Tokenize(string? text, List<string> into)
    {
        if (string.IsNullOrEmpty(text))
            return;

        var word = new StringBuilder();
        var previousCjk = '\0';

        void FlushWord()
        {
            if (word.Length >= 2)
                into.Add(word.ToString().ToLowerInvariant());
            word.Clear();
        }

        foreach (var c in text)
        {
            if (IsCjk(c))
            {
                FlushWord();
                into.Add(c.ToString());
                if (previousCjk != '\0')
                    into.Add(string.Concat(previousCjk, c));
                previousCjk = c;
                continue;
            }

            previousCjk = '\0';
            if (char.IsLetterOrDigit(c))
                word.Append(c);
            else
                FlushWord();
        }
        FlushWord();
    }

    private static bool IsCjk(char c) =>
        c is >= '一' and <= '鿿'      // CJK Unified Ideographs
          or >= '㐀' and <= '䶿'      // Extension A
          or >= '豈' and <= '﫿'      // Compatibility Ideographs
          or >= '぀' and <= 'ヿ';     // Hiragana / Katakana
}
