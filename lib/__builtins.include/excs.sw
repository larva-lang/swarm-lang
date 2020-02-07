public class TypeError
{
    var s;

    public func __init__(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(ValueError("需要字符串"));
        }
        this.s = s;
    }

    public func __str__()
    {
        return this.s;
    }
}

public class ValueError
{
    var s;

    public func __init__(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(ValueError("需要字符串"));
        }
        this.s = s;
    }

    public func __str__()
    {
        return this.s;
    }
}
