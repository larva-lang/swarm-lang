public class str
{
    !<<
    v   string
    !>>

    public func __init__(x)
    {
        var s = x.__str__();
        if (!isinstanceof(s, str))
        {
            throw(TypeError("‘__str__’方法返回的对象不是字符串"));
        }
        !<<
        this.v = l_s.v
        !>>
    }

    //todo
}

!<<

func sw_str_from_go_str(s string) *sw_cls_@<<:str>> {
    return &sw_cls_@<<:str>>{
        v:  s,
    }
}

!>>

public func repr(x)
{
    var s = x.__repr__();
    if (!isinstanceof(s, str))
    {
        throw(TypeError("‘__repr__’方法返回的对象不是字符串"));
    }
    return s;
}
