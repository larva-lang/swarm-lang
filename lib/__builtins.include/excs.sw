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

//不含数据的空异常类，可被其他类似异常扩展
public class EmptyException
{
    public func __init__()
    {
    }

    public func __str__()
    {
        return "";
    }
}

public class DivByZeroError(EmptyException)
{
    public func __str__()
    {
        return "被零除";
    }
}

public class ShiftByNegError(EmptyException)
{
    public func __str__()
    {
        return "移位数量为负";
    }
}

public class NotImpl(EmptyException)
{
    public func __str__()
    {
        return "未实现";
    }
}

public class IndexError
{
    var idx, sz;

    public func __init__(idx, sz)
    {
        if (!(isinstanceof(idx, int) && isinstanceof(sz, int)))
        {
            throw(TypeError("IndexError(idx, sz)的参数需要是两个int"));
        }
        this.idx    = idx;
        this.sz     = sz;
    }

    public func __str__()
    {
        return "索引%d在范围[0, %d)之外".(this.idx, this.sz);
    }
}

public class NoPerm(_Exception)
{
}

public class NoAttr(_Exception)
{
}

public class NoMethod(_Exception)
{
}
