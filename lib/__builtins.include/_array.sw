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
        var (start, end);
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
            return start + end;
        }

        var l = [start];
        for (var i: this)
        {
            l.append(repr(i));
            l.append(", ");
        }
        l[-1] = end;
        return "".join(l);
    }

    public func __bool__()
    {
        return this.size() != 0;
    }

    public func __getelem__(idx)
    {
        var real_idx = _make_array_real_idx("%T".(this), idx, this.size());
        !<<
        i := l_real_idx.(*sw_cls_@<<:int>>).v
        return this.v[i]
        !>>
    }

    public func __getslice__(bi, ei)
    {
        (bi, ei) = _make_array_real_slice_range("%T".(this), bi, ei, this.size());
        !<<
        b := l_bi.(*sw_cls_@<<:int>>).v
        e := l_ei.(*sw_cls_@<<:int>>).v
        s := this.v[b : e]
        !>>
        if (isinstanceof(this, tuple))
        {
            !<<
            return sw_obj_tuple_from_go_slice(s)
            !>>
        }
        else if (isinstanceof(this, list))
        {
            !<<
            return sw_obj_list_from_go_slice(s)
            !>>
        }
        else
        {
            abort("bug");
        }
    }

    public func _cmp_oper(op, other)
    {
        var do_cmp = func () {
            var (this_sz, other_sz) = (this.size(), other.size());
            if (op == "==" && this_sz != other_sz)
            {
                return false;
            }
            for (var i: range(0, min(this_sz, other_sz)))
            {
                if ((op == "<" && this[i] >= other[i]) || (op == "==" && this[i] != other[i]))
                {
                    return false;
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

    public func __lt__(other)
    {
        return this._cmp_oper("<", other);
    }

    public func __eq__(other)
    {
        return this._cmp_oper("==", other);
    }

    public func __add__(other)
    {
        //todo
        throw(NotImpl());
    }

    public func __mul__(other)
    {
        //todo
        throw(NotImpl());
    }

    public func size()
    {
        !<<
        return sw_obj_int_from_go_int(int64(len(this.v)))
        !>>
    }

    public func has(x)
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

func _make_array_real_idx(type_name, idx, sz)
{
    if (!isinstanceof(idx, int))
    {
        throw(TypeError("%s[x]的下标需要是int类型".(type_name)));
    }
    var real_idx = idx + sz if idx < 0 else idx;
    if (real_idx < 0 || real_idx >= sz)
    {
        throw(IndexError(idx, sz));
    }
    return real_idx;
}

func _make_array_real_slice_range(type_name, bi, ei, sz)
{
    if (bi is nil)
    {
        bi = 0;
    }
    if (ei is nil)
    {
        ei = sz;
    }

    if (!(isinstanceof(bi, int) && isinstanceof(ei, int)))
    {
        throw(TypeError("%s[x:y]的两个下标需要是nil或int对象".(type_name)));
    }

    var fix_idx = func (i) {
        if (i < 0)
        {
            i += sz;
        }
        return min(max(0, i), sz);
    };
    bi = fix_idx.call(bi);
    ei = fix_idx.call(ei);
    if (bi > ei)
    {
        ei = bi;
    }
    return (bi, ei);
}

!<<

func sw_util_copy_go_slice(s []sw_obj) []sw_obj {
    new_s := make([]sw_obj, len(s))
    copy(new_s, s)
    return new_s
}

!>>
