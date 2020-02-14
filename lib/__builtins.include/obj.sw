!<<

/*
sw_obj是一个所有对象的句柄类型，是一个interface，包含了程序涉及到的所有可能的方法，因此不能写在代码中，而是由编译器生成在util代码中
*/
//type sw_obj interface {...}

func sw_obj_cmp(a, b sw_obj) int64 {
    return sw_func_@<<:cmp>>_2(a, b).(*sw_cls_@<<:int>>).v
}

func sw_obj_eq(a, b sw_obj) bool {
    return sw_func_@<<:eq>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

!>>

public func cmp(a, b)
{
    var result = a.__cmp__(b);
    if (!isinstanceof(result, int))
    {
        throw(TypeError("‘__cmp__’方法返回的对象不是int类型"));
    }
    return result;
}

public func eq(a, b)
{
    var result = a.__eq__(b);
    if (!isinstanceof(result, bool))
    {
        throw(TypeError("‘__eq__’方法返回的对象不是bool类型"));
    }
    return result;
}
