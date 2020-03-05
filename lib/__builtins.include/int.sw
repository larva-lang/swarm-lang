!<<

type sw_cls_int int64

func sw_obj_int_from_go_int(x int64) sw_cls_int {
    return sw_cls_int(x)
}

func (si sw_cls_int) type_name() string {
    return "int"
}

func (si sw_cls_int) addr() uint64 {
    return 0
}

func (si sw_cls_int) sw_method___repr__(perm int64, args ...sw_obj) sw_obj {
    if len(args) != 0 {
        sw_util_abort_on_method_arg_count_err(len(args), 0)
    }
    return sw_obj_str_from_go_str(fmt.Sprintf("%d", int64(si)))
}

func (si sw_cls_int) sw_method___str__(perm int64, args ...sw_obj) sw_obj {
    return si.sw_method___repr__(perm, args...)
}

!>>

public func int_obj(x int)
{
    !<<
    return sw_obj_int_from_go_int(l_x)
    !>>
}
