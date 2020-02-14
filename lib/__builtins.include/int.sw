public class int
{
    !<<
    v   int64
    !>>

    //todo
}

!<<

func sw_obj_int_from_go_int(i int64) *sw_cls_@<<:int>> {
    return &sw_cls_@<<:int>>{
        v:  i,
    }
}

!>>
