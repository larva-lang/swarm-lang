public class range
{
    var curr int, end int;

    public func __init__(begin int, end int)
    {
        this.curr   = begin;
        this.end    = end;
    }

    public func is_valid() bool
    {
        return this.curr < this.end;
    }

    public func iter()
    {
        return this;
    }

    public func next() int
    {
        var ret = this.curr;
        this.curr = this.curr + 1;
        return ret;
    }
}
