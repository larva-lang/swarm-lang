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

func sw_util_sprintf(format string, args ...[]interface{}) string {
    return fmt.Sprintf(format, args...)
}

func sw_util_obj_addr(x sw_obj) uint64 {
    return uint64(reflect.ValueOf(&x).Elem().InterfaceData()[1])
}

!>>
