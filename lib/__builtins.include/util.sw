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

var (
    sw_util_true    int64 = 1
    sw_util_false   int64 = 0
)

func sw_util_isinstanceof_int(x sw_obj) int64 {
    if _, ok := x.(sw_cls_int); ok {
        return 1
    } else {
        return 0
    }
}

!>>

/* 后续再支持

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

*/
