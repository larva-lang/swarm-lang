public func map(it, f)
{
    var r = [];
    for (var i: it)
    {
        r.append(f.call(i));
    }
    return r;
}
