!<<

type sw_fo_stru struct {
    f func (perm int64, args ...sw_obj) sw_obj
}

func (fo *sw_fo_stru) type_name() string {
    return "func"
}

func (fo *sw_fo_stru) addr() uint64 {
    return sw_util_obj_addr(fo)
}

func (fo *sw_fo_stru) sw_method___repr__(perm int64, args ...sw_obj) sw_obj {
    if len(args) != 0 {
        sw_util_abort_on_method_arg_count_err(len(args), 0)
    }
    return sw_obj_str_from_go_str(fmt.Sprintf("<func obj at 0x%X>", fo.addr()))
}

func (fo *sw_fo_stru) sw_method___str__(perm int64, args ...sw_obj) sw_obj {
    return fo.sw_method___repr__(perm, args...)
}

func (fo *sw_fo_stru) sw_method_call(perm int64, args ...sw_obj) sw_obj {
    return fo.f(perm, args...)
}

!>>
