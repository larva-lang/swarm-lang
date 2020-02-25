public class NilType
{
    public func __repr__()
    {
        return "nil";
    }

    public func __bool__()
    {
        return 0;
    }

    public func __eq__(other)
    {
        return other is nil;
    }
}

!<<

var sw_util_nil_obj sw_obj

//主要用于初始化时候，用函数获取的方式来保证nil对象的全局唯一性
func sw_obj_get_nil() sw_obj {
    if sw_util_nil_obj.ov == nil {
        sw_util_nil_obj.ov = &sw_cls_@<<:NilType>>{}
    }
    return sw_util_nil_obj
}

!>>
