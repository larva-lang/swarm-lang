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
