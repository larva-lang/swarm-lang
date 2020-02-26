!<<

func sw_obj_int_from_go_bool(b bool) sw_cls_int {
    if b {
        return 1
    } else {
        return 0
    }
}

func sw_obj_to_go_bool(x sw_obj) bool {
    return x.(sw_cls_int) != 0
}

!>>
