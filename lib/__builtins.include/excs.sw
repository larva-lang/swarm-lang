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
    var info;

    public func __str__()
    {
        return info;
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
        return info;
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
        return info;
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
