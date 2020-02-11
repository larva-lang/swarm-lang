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

public class NoPerm
{
    public func __str__()
    {
        return "对属性或方法没有操作权限";
    }
}

final var _exc_no_perm = NoPerm();
