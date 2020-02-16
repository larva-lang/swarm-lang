public class list(_Array)
{
    //todo

    public func __setelem__(idx, x)
    {
        var real_idx = _make_array_real_idx("list", idx, this.size());
        !<<
        i := l_real_idx.(*sw_cls_@<<:int>>).v
        this.v[i] = l_x
        !>>
    }

    public func __setslice__(bi, ei, it)
    {
        (bi, ei) = _make_array_real_slice_range("list", bi, ei, this.size());
        var l = list(it);
        //todo
        throw(NotImpl());
    }

    public func __iadd__(other)
    {
        //todo
        throw(NotImpl());
    }

    public func __imul__(other)
    {
        //todo
        throw(NotImpl());
    }

    public func append(e)
    {
        !<<
        this.v = append(this.v, l_e)
        !>>
        return this;
    }

    public func pop(idx)
    {
        var real_idx = _make_array_real_idx("list", idx, this.size());
        !<<
        i := l_real_idx.(*sw_cls_@<<:int>>).v
        this.v = append(this.v[: i], this.v[i + 1 :]...)
        !>>
        return this;
    }

    public func pop()
    {
        return this.pop(-1);
    }

    public func iter()
    {
        return listiter(this);
    }
}

class listiter(_ArrayIter)
{
}

!<<

func sw_obj_list_from_go_slice(s []sw_obj) *sw_cls_@<<:list>> {
    return &sw_cls_@<<:list>>{
        v:  sw_util_copy_go_slice(s),
    }
}

!>>
