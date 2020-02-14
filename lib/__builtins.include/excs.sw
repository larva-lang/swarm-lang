public class TypeError
{
    var s;

    public func __init__(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(TypeError("TypeError(x)的参数需要是字符串"));
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
            throw(TypeError("ValueError(x)的参数需要是字符串"));
        }
        this.s = s;
    }

    public func __str__()
    {
        return this.s;
    }
}

public class DivByZeroError
{
    public func __init__()
    {
    }

    public func __str__()
    {
        return "被零除";
    }
}

public class ShiftByNegError
{
    public func __init__()
    {
    }

    public func __str__()
    {
        return "移位数量为负";
    }
}

public class IndexError
{
    var idx, sz;

    public func __str__()
    {
        return "索引%d在范围[0, %d)之外".(this.idx, this.sz);
    }
}

public func throw_index_error(idx, sz)
{
    if (!(isinstanceof(idx, int) && isinstanceof(sz, int)))
    {
        throw(TypeError("throw_index_error(idx, sz)的参数需要是两个int"));
    }
    exc = IndexError();
    exc.idx = idx;
    exc.sz  = sz;
    return exc;
}

public class NoPerm
{
    var info;

    public func __str__()
    {
        return this.info;
    }
}

!<<

func sw_exc_make_no_perm_exc(info string) sw_obj {
    return &sw_cls_@<<:NoPerm>>{
        m_info: &sw_cls_@<<:str>>{
            v:  info,
        },
    }
}

!>>

public class NoAttr
{
    var info;

    public func __str__()
    {
        return this.info;
    }
}

!<<

func sw_exc_make_no_attr_exc(info string) sw_obj {
    return &sw_cls_@<<:NoAttr>>{
        m_info: &sw_cls_@<<:str>>{
            v:  info,
        },
    }
}

!>>

public class NoMethod
{
    var info;

    public func __str__()
    {
        return this.info;
    }
}

!<<

func sw_exc_make_no_method_exc(info string) sw_obj {
    return &sw_cls_@<<:NoMethod>>{
        m_info: &sw_cls_@<<:str>>{
            v:  info,
        },
    }
}

!>>
