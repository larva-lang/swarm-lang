public class NilType
{
    //todo
}

!<<

var sw_util_nil_obj sw_obj

//主要用于初始化时候，用函数获取的方式来保证nil对象的全局唯一性
func sw_obj_get_nil() sw_obj {
    if sw_util_nil_obj == nil {
        sw_util_nil_obj = &sw_cls_@<<:NilType>>{}
    }
    return sw_util_nil_obj
}

!>>
