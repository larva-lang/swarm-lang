public class tuple(_Array)
{
    //todo

    public func hash()
    {
        //todo
        throw(NotImpl());
    }

    public func iter()
    {
        return tupleiter(this);
    }
}

class tupleiter(_ArrayIter)
{
}

!<<

func sw_obj_tuple_from_go_slice(s []sw_obj, need_copy bool) *sw_cls_@<<:tuple>> {
    if need_copy {
        s = sw_util_copy_go_slice(s)
    }
    return &sw_cls_@<<:tuple>>{
        v:  s,
    }
}

!>>
