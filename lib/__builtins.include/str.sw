public class str
{
    !<<
    s   string
    !>>

    //todo
}

!<<

func sw_str_from_go_str(s string) *sw_cls_@<<:str>> {
    return &sw_cls_@<<:str>>{
        s:  s,
    }
}

!>>
