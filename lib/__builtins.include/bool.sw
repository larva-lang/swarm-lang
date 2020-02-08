public class bool
{
    !<<
    v   bool
    !>>

    //bool的构造需要保证true或false的唯一性，由编译器特殊处理，不能直接实现，编译器对于代码bool(x)会调用到下面的cast_to_bool(x)
    //func __init__(x)

    //todo
}

func cast_to_bool(x)
{
    var b = x.__bool__();
    if (!isinstanceof(b, bool))
    {
        throw(TypeError("‘__bool__’方法返回的对象不是bool对象"));
    }
    if (!(b is _bool_obj_true || b is _bool_obj_false))
    {
        abort("bool对象失去了唯一性");
    }
    return b;
}

final var (_bool_obj_true, _bool_obj_false);

!<<

/*
编译器保证输出的所有全局变量的初始化在sw_env_init_mod_*函数中，因此这个init是肯定在那之前执行的
在这个init之前执行的只有Go层面的全局变量初值赋值，都统一赋值为sw_obj_get_nil()，不会依赖true和false
*/
func init() {
    sw_gv_@<<:_bool_obj_true>>  = &sw_cls_@<<:bool>>{v: true}
    sw_gv_@<<:_bool_obj_false>> = &sw_cls_@<<:bool>>{v: false}
}

!>>
