//用于双目运算不支持时的异常抛出，简化开发
public func throw_unsupported_binocular_oper(op, a, b)
{
    throw(TypeError("不支持类型‘%T’和‘%T’的‘%s’运算".(a, b, op)));
}

func _cmp_oper(op, a, b)
{
    var result;
    if (op == "lt")
    {
        result = a.__lt__(b);
    }
    else if (op == "eq")
    {
        result = a.__eq__(b);
    }
    else
    {
        abort("bug");
    }
    if (!isinstanceof(result, bool))
    {
        throw(TypeError("‘__%s__’方法返回的对象不是bool类型".(op)));
    }
    return result;
}

public func less_than(a, b)
{
    return _cmp_oper("lt", a, b);
}

public func equals(a, b)
{
    return _cmp_oper("eq", a, b);
}

!<<

func sw_obj_lt(a, b sw_obj) bool {
    return sw_func_@<<:less_than>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

func sw_obj_eq(a, b sw_obj) bool {
    return sw_func_@<<:equals>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

!>>
