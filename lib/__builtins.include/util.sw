//直接令程序崩溃，参数s需要是str
public func abort(s)
{
    !<<
    s, ok := l_s.ov.(*sw_cls_@<<:str>>)
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
    return uint64(reflect.ValueOf(&x.ov).Elem().InterfaceData()[1])
}

func sw_util_to_go_fmt_str(format string, x sw_obj) string {
    switch format {
    case "%T":
        return x.type_name()
    case "%s":
        return sw_obj_to_go_str(x)
    case "%r":
        return sw_func_@<<:repr>>_1(x).go_str()
    }

    switch o := x.ov.(type) {
    case nil:
        switch format {
        case "%t":
            return fmt.Sprintf(format, x.iv != 0)
        case "%c", "%d":
            if format != "%c" || (x.iv >= 0 && x.iv <= 0xFF) {
                return fmt.Sprintf(format, x.iv)
            }
        case "%b", "%o", "%x", "%X":
            return fmt.Sprintf(format, uint64(x.iv))
        }
    case *sw_cls_@<<:float>>:
        switch format {
        case "%b", "%x", "%X", "%e", "%E", "%f", "%F", "%g", "%G":
            return fmt.Sprintf(format, o.v)
        }
    case *sw_cls_@<<:str>>:
        switch format {
        case "%x", "%X":
            return fmt.Sprintf(format, o.v)
        }
    }

    err_info := fmt.Sprintf("格式‘%s’不能匹配类型‘%s’或对应的值", format, x.type_name())
    sw_func_@<<:throw>>_1(sw_new_obj_sw_cls_@<<:ValueError>>_1(sw_obj_str_from_go_str(err_info)))
    panic("bug")
}

!>>

func _unpack_multi_value(it, count)
{
    var vs = [];
    it = it.iter();
    while (it)
    {
        if (vs.size() >= count)
        {
            throw(ValueError("表达式解包解出的值过多，需要%d个".(count)));
        }
        vs.append(it.next());
    }
    if (vs.size() < count)
    {
        throw(ValueError("表达式解包解出的值过少，需要%d个，解出%d个".(count, vs.size())));
    }
    return vs;
}
