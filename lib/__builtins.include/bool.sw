public class bool
{
    !<<
    v   bool
    !>>

    //func __init__(x)  //bool的构造需要保证true或false的唯一性，由编译器特殊处理，不能直接实现

    //todo
}

final var (bool_obj_true, bool_obj_false);

!<<

/*
编译器保证输出的所有全局变量的初始化在sw_env_init_mod_*函数中，因此这个init是肯定在那之前执行的
在这个init之前执行的只有Go层面的全局变量初值赋值，都统一赋值为sw_obj_get_nil()，不会依赖true和false
*/
func init() {
    sw_gv_@<<:bool_obj_true>>   = &sw_cls_@<<:bool>>{v: true}
    sw_gv_@<<:bool_obj_false>>  = &sw_cls_@<<:bool>>{v: false}
}

!>>
