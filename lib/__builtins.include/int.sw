!<<

type sw_cls_int int64

func (si sw_cls_int) sw_method___repr__(perm int64, args ...sw_obj) sw_obj {
    if len(args) != 0 {
        sw_util_abort_on_method_arg_count_err(len(args), 0)
    }
    return sw_obj_str_from_go_str(fmt.Sprintf("%d", si))
}

!>>
