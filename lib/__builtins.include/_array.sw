//基于数组的数据结构，用于tuple和list的扩展源
class _Array
{
    !<<
    v   []sw_obj
    !>>

    public func __init__(it)
    {
        !<<
        this.v = make([]sw_obj, 0, 4)
        !>>
        for (var i: it)
        {
            !<<
            this.v = append(this.v, l_i)
            !>>
        }
    }

    public func __repr__()
    {
        var start, end;
        if (isinstanceof(this, tuple))
        {
            start   = "(";
            end     = ")";
        }
        else if (isinstanceof(this, list))
        {
            start   = "[";
            end     = "]";
        }
        else
        {
            abort("bug");
        }

        if (this.size() == 0)
        {
            return start.concat(end);
        }

        var l = [start];
        for (var i: this)
        {
            l.append(repr(i));
            l.append(", ");
        }
        l.set(l.size() - 1, end);
        return "".join(l);
    }

    public func get(idx int)
    {
        _throw_on_idx_err(idx, this.size());
        !<<
        return this.v[l_idx]
        !>>
    }

    public func slice(bi int, ei int)
    {
        var sz = this.size();
        _throw_on_idx_err(bi, sz);
        _throw_on_idx_err(ei, sz);
        !<<
        s := this.v[l_bi : l_ei]
        !>>
        if (isinstanceof(this, tuple))
        {
            !<<
            return sw_obj_tuple_from_go_slice(s, true)
            !>>
        }
        else if (isinstanceof(this, list))
        {
            !<<
            return sw_obj_list_from_go_slice(s, true)
            !>>
        }
        else
        {
            abort("bug");
        }
    }

    public func _cmp_oper(op, other) int
    {
        var op_is_lt = op.eq("<").int,
            op_is_eq = !op_is_lt,
        ;

        var do_cmp = func () int {
            var this_sz     = this.size(),
                other_sz    = other.size().int,
            ;
            if (op_is_eq && this_sz != other_sz)
            {
                return 0;
            }
            for (var i: range(0, min(this_sz, other_sz)))
            {
                if ((op_is_lt && this.get(i).cmp(other.get(i)) >= 0) || (op_is_eq && !this.get(i).eq(other.get(i)).int))
                {
                    return 0;
                }
            }
            return this_sz <= other_sz;
        };

        if (isinstanceof(this, tuple))
        {
            if (isinstanceof(other, tuple))
            {
                do_cmp.call();
            }
        }
        else if (isinstanceof(this, list))
        {
            if (isinstanceof(other, list))
            {
                do_cmp.call();
            }
        }
        else
        {
            abort("bug");
        }

        throw_unsupported_binocular_oper(op, this, other);
    }

    public func lt(other) int
    {
        return this._cmp_oper("<", other);
    }

    public func eq(other) int
    {
        return this._cmp_oper("==", other);
    }

    //todo below

    public func __mul__(other)
    {
        if (isinstanceof(other, int))
        {
            !<<
            this_len    := int64(len(this.v))
            count       := l_other.(*sw_cls_@<<:int>>).v
            if count < 0 || (count > 0 && this_len * count / count != this_len) {
            !>>
                throw(ValueError("‘%T*count’运算参数错误，count=%d，容器大小=%d".(this, other, this.size())));
            !<<
            }
            new_s := make([]sw_obj, 0, this_len * count)
            for i := int64(0); i < count; i ++ {
                new_s = append(new_s, this.v...)
            }
            !>>
            if (isinstanceof(this, tuple))
            {
                !<<
                return sw_obj_tuple_from_go_slice(new_s, false)
                !>>
            }
            else if (isinstanceof(this, list))
            {
                !<<
                return sw_obj_list_from_go_slice(new_s, false)
                !>>
            }
            else
            {
                abort("bug");
            }
        }

        throw_unsupported_binocular_oper("*", this, other);
    }

    public func size() int
    {
        !<<
        return sw_cls_int(int64(len(this.v)))
        !>>
    }

    public func has(x) int
    {
        //todo
        throw(NotImpl());
    }
}

//用于tuple和list的迭代器的扩展源
class _ArrayIter
{
    var a, curr_idx;

    func __init__(a)
    {
        this.a          = a;
        this.curr_idx   = 0;
    }

    public func __bool__()
    {
        return this.curr_idx < this.a.size();
    }

    public func next()
    {
        var curr = this.a[this.curr_idx];
        this.curr_idx += 1;
        return curr;
    }
}

func _throw_on_idx_err(idx int, sz int)
{
    if (idx < 0 || idx >= sz)
    {
        throw(IndexError(idx, sz));
    }
}

!<<

func sw_util_copy_go_slice(s []sw_obj) []sw_obj {
    new_s := make([]sw_obj, len(s))
    copy(new_s, s)
    return new_s
}

!>>
