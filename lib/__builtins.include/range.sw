public class range
{
    var curr, end;

    public func __init__(begin, end)
    {
        this.curr   = begin;
        this.end    = end;
    }

    public func iter()
    {
        return this;
    }

    public func get()
    {
        return this.curr;
    }

    public func can_get()
    {
        return this.curr < this.end;
    }

    public func inc()
    {
        this.curr += 1;
    }
}
