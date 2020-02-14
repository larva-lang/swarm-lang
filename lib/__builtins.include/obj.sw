!<<

/*
sw_obj是一个所有对象的句柄类型，是一个interface，包含了程序涉及到的所有可能的方法，因此不能写在代码中，而是由编译器生成在util代码中
*/
//type sw_obj interface {...}

func sw_obj_lt(a, b sw_obj) bool {
    return sw_func_@<<:less_than>>_2(a, b).(*sw_cls_@<<:int>>).v
}

func sw_obj_eq(a, b sw_obj) bool {
    return sw_func_@<<:equals>>_2(a, b).(*sw_cls_@<<:bool>>).v
}

!>>

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
