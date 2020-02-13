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
    case "%r":
        return sw_func_@<<:repr>>_1(x).(*sw_cls_@<<:str>>).v
    }

    switch o := x.(type) {
    case sw_cls_@<<:bool>>:
        if format == "%t" {
            return fmt.Sprintf(format, o.v)
        }
    case sw_cls_@<<:int>>:
        switch format {
        case "%b", "%c", "%d", "%o", "%x", "%X":
            if format != "%c" || (o.v >= 0 && o.v <= 0xFF) {
                return fmt.Sprintf(format, o.v)
            }
        }
    case sw_cls_@<<:uint>>:
        switch format {
        case "%b", "%c", "%d", "%o", "%x", "%X":
            if format != "%c" || (o.v >= 0 && o.v <= 0xFF) {
                return fmt.Sprintf(format, o.v)
            }
        }
    case sw_cls_@<<:float>>:
        switch format {
        case "%b", "%x", "%X", "%e", "%E", "%f", "%F", "%g", "%G":
            return fmt.Sprintf(format, o.v)
        }
    case sw_cls_@<<:str>>:
        switch format {
        case "%x", "%X":
            return fmt.Sprintf(format, o.v)
        }
    }

    err_info := fmt.Sprintf("格式‘%s’不能匹配类型‘%s’或对应的值", format, x.type_name())
    sw_func_@<<:throw>>_1(sw_new_obj_sw_cls_@<<:ValueError>>_1(sw_str_from_go_str(err_info)))
    panic("bug")
}

!>>

func _unpack_multi_value(it, count)
{
    var vs = [];
    it = it.iter();
    while (it.can_get())
    {
        if (vs.size() >= count)
        {
            throw(ValueError("表达式解包出的值过多，需要%d个".(count)));
        }
        vs.append(it.get());
        it.inc();
    }
    return vs;
}
