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
