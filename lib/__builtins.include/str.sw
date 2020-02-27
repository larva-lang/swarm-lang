func _to_str(method, x)
{
    var s;
    if (method.eq("str"))
    {
        s = x.__str__();
    }
    else if (method.eq("repr"))
    {
        s = x.__repr__();
    }
    else
    {
        abort("bug");
    }
    if (!isinstanceof(s, str))
    {
        throw(TypeError("‘__%s__’方法返回的对象不是字符串".(method)));
    }
    return s;
}

public func repr(x)
{
    return _to_str("repr", x);
}

public class str
{
    !<<
    v   string
    !>>

    public func __init__(x)
    {
        var s = _to_str("str", x);
        !<<
        this.v = sw_obj_str_to_go_str(l_s)
        !>>
    }

    public func __repr__()
    {
        !<<
        return sw_obj_str_from_go_str(fmt.Sprintf("%q", this.v))
        !>>
    }

    public func __str__()
    {
        return this;
    }

    public func char_at(idx int) int
    {
        _throw_on_idx_err(idx, this.len());
        !<<
        return sw_cls_int(this.v[l_idx])
        !>>
    }

    public func sub_str(bi int, ei int)
    {
        var this_len = this.len();
        _throw_on_idx_err(bi, this_len);
        _throw_on_idx_err(ei, this_len);
        !<<
        return sw_obj_str_from_go_str(this.v[l_bi : l_ei])
        !>>
    }

    public func cmp(other) int
    {
        if (isinstanceof(other, str))
        {
            !<<
            v := sw_obj_str_to_go_str(l_other)
            if this.v < other.v {
                return sw_cls_int(-1)
            } else if this.v > other.v {
                return sw_cls_int(1)
            } else {
                return sw_cls_int(0)
            }
            !>>
        }
        throw_unsupported_binocular_oper("比较", this, other);
    }

    public func eq(other) int
    {
        if (isinstanceof(other, str))
        {
            !<<
            v := sw_obj_str_to_go_str(l_other)
            if this.v == other.v {
                return sw_cls_int(1)
            } else {
                return sw_cls_int(0)
            }
            !>>
        }
        throw_unsupported_binocular_oper("判等", this, other);
    }

    public func concat(other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            return sw_obj_str_from_go_str(this.v + sw_obj_str_to_go_str(l_other))
            !>>
        }

        throw_unsupported_binocular_oper("连接", this, other);
    }

    public func repeat(count int)
    {
        var this_len = this.len();
        _throw_on_repeat_count_err(count, this_len);
        !<<
        return sw_obj_str_from_go_str(strings.Repeat(this.v, int(l_count)))
        !>>
    }

    public func len() int
    {
        !<<
        return sw_cls_int(int64(len(this.v)))
        !>>
    }

    public func has(s) int
    {
        if (!isinstanceof(s, str))
        {
            throw(TypeError("str.has(x)的参数需要是字符串"));
        }

        !<<
        v := sw_obj_str_to_go_str(l_s)
        if strings.Contains(this.v, v) {
            return sw_cls_int(1)
        } else {
            return sw_cls_int(0)
        }
        !>>
    }

    public func hash() int
    {
        //todo
        throw(NotImpl());
    }

    public func join(it)
    {
        !<<
        sl := make([]string, 0, 8)
        !>>
        for (var s: it)
        {
            if (!isinstanceof(s, str))
            {
                throw(TypeError("str.join(iterable)的参数的迭代元素必须是字符串"));
            }
            !<<
            sl = append(sl, sw_obj_str_to_go_str(l_s))
            !>>
        }
        !<<
        return sw_obj_str_from_go_str(strings.Join(sl, this.v))
        !>>
    }
}

!<<

func sw_obj_str_from_go_str(s string) *sw_cls_@<<:str>> {
    return &sw_cls_@<<:str>>{
        v:  s,
    }
}

func sw_obj_to_go_str(obj sw_obj) string {
    //直接构造str对象并返回其内部value
    return sw_new_obj_sw_cls_@<<:str>>_1(obj).v
}

func sw_obj_str_to_go_str(x sw_obj) string {
    return x.(*sw_cls_@<<:str>>).v
}

!>>
