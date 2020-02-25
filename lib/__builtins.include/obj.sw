!<<

func sw_obj_to_go_bool(x sw_obj) bool {
    return sw_func_@<<:_cast_to_bool>>_1(x).iv != 0
}

func sw_obj_bool_from_go_bool(b bool) sw_obj {
    if b {
        return sw_obj{iv: 1}
    } else {
        return sw_obj{iv: 0}
    }
}

func sw_obj_assert_int(x sw_obj) {
    if x.ov != nil {
        panic("assert int failed")
    }
}

func sw_obj_assert_non_int(x sw_obj) {
    if x.ov == nil {
        panic("assert non-int failed")
    }
}

type sw_obj struct {
    iv  int64
    ov  sw_obj_intf
}

func (so sw_obj) go_bool() bool {
    sw_obj_assert_int(so)
    return so.iv != 0
}

func (so sw_obj) go_int() int64 {
    sw_obj_assert_int(so)
    return so.iv
}

func (so sw_obj) go_str() string {
    sw_obj_assert_non_int(so)
    return so.ov.(*sw_cls_@<<:str>>).v
}

!>>

func _cast_to_bool(x)
{
    x = x.__bool__();
    !<<
    if l_x.go_bool() {
    !>>
        return 1;
    !<<
    } else {
    !>>
        return 0;
    !<<
    }
    !>>
}

//用于‘!’运算
func _cast_to_bool_not(x)
{
    return 0 if x else 1;
}
