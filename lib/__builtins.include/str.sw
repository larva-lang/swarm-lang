public class str
{
    !<<
    v   string
    !>>

    public func __init__(x)
    {
        var s = x.__str__();
        if (!isinstanceof(s, str))
        {
            throw(TypeError("‘__str__’方法返回的对象不是字符串"));
        }
        !<<
        this.v = l_s.v
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

    public func __bool__()
    {
        return this.len() != 0;
    }

    public func __getelem__(idx)
    {
        if (!isinstanceof(idx, int))
        {
            throw(TypeError("str[x]的下标需要是int类型"));
        }
        var len = this.len();
        var real_idx = idx + len if idx < 0 else idx;
        if (real_idx < 0 || real_idx >= len)
        {
            throw_index_error(idx, len);
        }
        !<<
        i := l_real_idx.(*sw_cls_@<<:int>>).v
        return sw_obj_str_from_go_str(this.v[i : i + 1])
        !>>
    }

    public func __getslice__(bi, ei)
    {
        var len = this.len();
        if (bi is nil)
        {
            bi = 0;
        }
        if (ei is nil)
        {
            ei = len;
        }

        if (!(isinstanceof(bi, int) && isinstanceof(ei, int)))
        {
            throw(TypeError("str[x:y]的两个下标需要是nil或int对象"));
        }

        var fix_idx = func (i) {
            if (i < 0)
            {
                i += len;
            }
            return min(max(0, i), len);
        };
        bi = fix_idx.call(bi);
        ei = fix_idx.call(ei);
        if (bi > ei)
        {
            ei = bi;
        }
        !<<
        b := l_bi.(*sw_cls_@<<:int>>).v
        e := l_ei.(*sw_cls_@<<:int>>).v
        return sw_obj_str_from_go_str(this.v[b : e])
        !>>
    }

    public func __lt__(other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            return sw_obj_bool_from_go_bool(this.v < l_other.(*sw_cls_@<<:str>>).v)
            !>>
        }

        throw_unsupported_binocular_oper("<", this, other);
    }

    public func __eq__(other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            return sw_obj_bool_from_go_bool(this.v == l_other.(*sw_cls_@<<:str>>).v)
            !>>
        }

        throw_unsupported_binocular_oper("==", this, other);
    }

    public func __add__(other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            return sw_obj_str_from_go_str(this.v + l_other.(*sw_cls_@<<:str>>).v)
            !>>
        }

        throw_unsupported_binocular_oper("+", this, other);
    }

    public func __mul__(other)
    {
        if (isinstanceof(other, int))
        {
            !<<
            this_len    := int64(len(this.v))
            count       := l_other.(*sw_cls_@<<:int>>).v
            if count < 0 || (count > 0 && this_len * count / count != s_len) {
            !>>
                throw(ValueError("‘str*count’运算参数错误，count=%d，字符串长度=%d".(other, this.len())));
            !<<
            }
            return sw_obj_str_from_go_str(strings.Repeat(this.v, int(count)))
            !>>
        }

        throw_unsupported_binocular_oper("*", this, other);
    }

    public func len()
    {
        !<<
        return sw_obj_int_from_go_int(int64(len(this.v)))
        !>>
    }

    public func has(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(TypeError("str.has(x)的参数需要是字符串"));
        }

        !<<
        v := l_s.(*sw_cls_@<<:str>>).v
        if strings.Contains(this.v, v) {
        !>>
            return true;
        !<<
        } else {
        !>>
            return false;
        !<<
        }
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

!>>

public func repr(x)
{
    var s = x.__repr__();
    if (!isinstanceof(s, str))
    {
        throw(TypeError("‘__repr__’方法返回的对象不是字符串"));
    }
    return s;
}
