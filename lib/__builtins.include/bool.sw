!<<

type sw_cls_bool bool

func sw_obj_bool_from_go_bool(x bool) sw_cls_bool {
    return sw_cls_bool(x)
}

func (sb sw_cls_bool) type_name() string {
    return "bool"
}

func (sb sw_cls_bool) addr() uint64 {
    return 0
}

func (sb sw_cls_bool) sw_method___repr__(perm int64, args ...sw_obj) sw_obj {
    if len(args) != 0 {
        sw_util_abort_on_method_arg_count_err(len(args), 0)
    }
    return sw_obj_str_from_go_str(fmt.Sprintf("%t", bool(sb)))
}

func (sb sw_cls_bool) sw_method___str__(perm int64, args ...sw_obj) sw_obj {
    return sb.sw_method___repr__(perm, args...)
}

!>>

public func bool_obj(x bool)
{
    !<<
    return sw_obj_bool_from_go_bool(l_x)
    !>>
}
