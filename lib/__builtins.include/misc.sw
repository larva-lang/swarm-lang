public func map(it, f)
{
    var r = [];
    for (var i: it)
    {
        r.append(f.call(i));
    }
    return r;
}

public func min(a, b)
{
    return a if a < b else b;
}

public func max(a, b)
{
    return a if a > b else b;
}
