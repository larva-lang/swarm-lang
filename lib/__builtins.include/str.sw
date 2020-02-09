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

    public func has(s)
    {
        //todo
    }

    //todo
}

!<<

func sw_obj_str_from_go_str(s string) *sw_cls_@<<:str>> {
    return &sw_cls_@<<:str>>{
        v:  s,
    }
}

func sw_obj_to_go_str(obj sw_obj) string {
    //直接构造str对象并返回其内部value
    return sw_new_obj_sw_cls_@<<:str>>_1(obj).v
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
