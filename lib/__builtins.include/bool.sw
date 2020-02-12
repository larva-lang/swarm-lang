public class bool
{
    !<<
    v   bool
    !>>

    //bool的构造需要保证true或false的唯一性，由编译器特殊处理，不能直接实现，编译器对于代码bool(x)会调用到下面的_cast_to_bool(x)
    //func __init__(x)

    public func __repr__()
    {
        return "true" if (this) else "false";
    }

    public func __bool__()
    {
        return this;
    }

    public func __lt__(other)
    {
        if (isinstanceof(other, bool))
        {
            return !this && other;
        }
        throw_unsupported_binocular_oper("<", this, other);
    }

    public func __eq__(other)
    {
        if (isinstanceof(other, bool))
        {
            return (this && other) || (!this && !other);
        }
        throw_unsupported_binocular_oper("==", this, other);
    }
}

func _cast_to_bool(x)
{
    var b = x.__bool__();

    !<<
    if _, ok := l_b.(*sw_cls_@<<:bool>>); !ok {
    !>>
        throw(TypeError("‘__bool__’方法返回的对象不是bool类型"));
    !<<
    }
    !>>

    !<<
    if l_b != sw_gv_@<<:_bool_obj_true>> && l_b != sw_gv_@<<:_bool_obj_false>> {
    !>>
        abort("bool对象失去了唯一性");
    !<<
    }
    !>>

    return b;
}

//用于‘!’运算
func _cast_to_bool_not(x)
{
    return false if x else true;
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

func sw_obj_bool_from_go_bool(b bool) sw_obj {
    if b {
        return sw_gv_@<<:_bool_obj_true>>
    } else {
        return sw_gv_@<<:_bool_obj_false>>
    }
}

func sw_obj_to_go_bool(obj sw_obj) bool {
    return sw_func_@<<:_cast_to_bool>>_1(obj).(*sw_cls_@<<:bool>>).v
}

!>>
