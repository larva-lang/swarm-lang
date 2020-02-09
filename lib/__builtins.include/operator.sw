//用于双目运算不支持时的异常抛出，简化开发
public func throw_unsupported_binocular_oper(op, a, b)
{
    throw(TypeError("不支持类型‘%T’和‘%T’的‘%s’运算".(a, b, op)));
}

public func less_than(a, b)
{
    var result = a.__lt__(b);
    if (!isinstanceof(result, bool))
    {
        throw(TypeError("‘__lt__’方法返回的对象不是bool类型"));
    }
    return result;
}

public func equals(a, b)
{
    var result = a.__eq__(b);
    if (!isinstanceof(result, bool))
    {
        throw(TypeError("‘__eq__’方法返回的对象不是bool类型"));
    }
    return result;
}

!<<

func sw_obj_lt(a, b sw_obj) bool {
    return sw_func_@<<:less_than>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

func sw_obj_eq(a, b sw_obj) bool {
    return sw_func_@<<:equals>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

!>>
