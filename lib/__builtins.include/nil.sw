public class NilType
{
    //todo
}

final var nil_obj;

!<<

//主要用于初始化时候，由于‘nil_obj’也是一个普通的全局变量，需要保证在其他全局变量的默认初始化之前，用函数获取的方式来保证
func sw_obj_get_nil() sw_obj {
    if sw_gv_@<<:nil_obj>> == nil {
        sw_gv_@<<:nil_obj>> = &sw_cls_@<<:NilType>>{}
    }
    return sw_gv_@<<:nil_obj>>
}

!>>
