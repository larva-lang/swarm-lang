public class uint
{
    !<<
    v   uint64
    !>>

    //todo
}

!<<

func sw_obj_uint_from_go_uint(ui uint64) *sw_cls_@<<:uint>> {
    return &sw_cls_@<<:uint>>{
        v:  ui,
    }
}

!>>
