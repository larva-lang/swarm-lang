//只能内部创建的简单异常，用于内部使用以及简单异常的扩展源
class _Exception
{
    var s;

    public func __str__()
    {
        return this.s;
    }
}

//公开的简单异常，增加public构造方法
public class Exception(_Exception)
{
    public func __init__(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(TypeError("%T(x)的参数需要是字符串".(this)));
        }
        this.s = s;
    }
}

public class TypeError(Exception)
{
}

public class ValueError(Exception)
{
}

//用于一些独立信息的异常类的扩展源
class _EmptyException
{
    public func __init__()
    {
    }
}

public class NotImpl(_EmptyException)
{
    public func __str__()
    {
        return "未实现";
    }
}

public class IndexError
{
    var idx int, sz int;

    public func __init__(idx int, sz int)
    {
        this.idx    = idx;
        this.sz     = sz;
    }

    public func __str__()
    {
        return "索引%s在范围[0, %s)之外".(this.idx, this.sz);
    }
}
