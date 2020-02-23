public class range
{
    var curr, end;

    public func __init__(begin, end)
    {
        this.curr   = begin;
        this.end    = end;
    }

    public func __bool__()
    {
        return this.curr < this.end;
    }

    public func iter()
    {
        return this;
    }

    public func next()
    {
        var ret = this.curr;
        this.curr = this.curr + 1;
        return ret;
    }
}
