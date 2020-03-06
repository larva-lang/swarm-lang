public class list(_Array)
{
    public func set(idx int, x)
    {
        _throw_on_idx_err(idx, this.size());
        !<<
        this.v[l_idx] = l_x
        !>>
        return this;
    }

    public func clear()
    {
        !<<
        this.v = this.v[: 0]
        !>>
        return this;
    }

    public func extend(other)
    {
        //todo
        throw(NotImpl());
        return this;
    }

    public func append(e)
    {
        !<<
        this.v = append(this.v, l_e)
        !>>
        return this;
    }

    public func pop(idx int)
    {
        _throw_on_idx_err(idx, this.size());
        !<<
        elem := this.v[l_idx]
        this.v = append(this.v[: l_idx], this.v[l_idx + 1 :]...)
        return elem
        !>>
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

func sw_obj_list_from_go_slice(s []sw_obj, need_copy bool) *sw_cls_@<<:list>> {
    if need_copy {
        s = sw_util_copy_go_slice(s)
    }
    return &sw_cls_@<<:list>>{
        v:  s,
    }
}

!>>
