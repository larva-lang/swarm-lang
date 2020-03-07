//直接令程序崩溃，参数s需要是str
public func abort(s)
{
    !<<
    s, ok := l_s.(*sw_cls_@<<:str>>)
    if ok {
        panic(s.v)
    } else {
        panic("SWARM ABORT WITH NON-STR-OBJECT!")
    }
    !>>
}

!<<

func sw_util_sprintf(format string, args ...interface{}) string {
    return fmt.Sprintf(format, args...)
}

func sw_util_obj_addr(x sw_obj) uint64 {
    return uint64(reflect.ValueOf(&x).Elem().InterfaceData()[1])
}

func sw_util_to_go_fmt_str(format string, x sw_obj) string {
    switch format {
    case "%T":
        return x.type_name()
    case "%s":
        return sw_obj_to_go_str(x)
    }

    panic("bug")
}

func sw_util_isinstanceof_bool(x sw_obj) bool {
    _, ok := x.(sw_cls_bool)
    return ok
}

func sw_util_isinstanceof_int(x sw_obj) bool {
    _, ok := x.(sw_cls_int)
    return ok
}

func sw_util_abort_on_method_arg_count_err(arg_count int, need_count int) {
    panic(fmt.Sprintf("参数数量错误，需要%d个，传入%d个", need_count, arg_count))
}

!>>

func _unpack_multi_value(it, count int)
{
    !<<
    var vs []sw_obj
    switch o := l_it.(type) {
    case *sw_cls_@<<:tuple>>:
        vs = o.v
    case *sw_cls_@<<:list>>:
        vs = o.v
    default:
        vs = make([]sw_obj, 0, l_count + 1)
    !>>
        it = it.iter();
        while (it.is_valid().bool)
        {
            !<<
            if int64(len(vs)) >= l_count {
                vs = append(vs, nil)    //多插入一个元素，作为错误标志
                break
            }
            !>>
            var elem = it.next();
            !<<
            vs = append(vs, l_elem)
            !>>
        }
    !<<
    }
    !>>
    var vs_len int;
    !<<
    l_vs_len = int64(len(vs))
    !>>
    if (vs_len > count)
    {
        throw(ValueError("表达式解包解出的值过多，需要%s个".(count)));
    }
    if (vs_len < count)
    {
        throw(ValueError("表达式解包解出的值过少，需要%s个，解出%s个".(count, vs_len)));
    }
    !<<
    return sw_obj_tuple_from_go_slice(vs, false)
    !>>
}
