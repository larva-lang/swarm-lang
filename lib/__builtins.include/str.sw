func _to_str(method, x)
{
    var s;
    if (method == "str")
    {
        s = x.__str__();
    }
    else if (method == "repr")
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
        var real_idx = _make_array_real_idx("str", idx, this.len());
        !<<
        i := l_real_idx.(*sw_cls_@<<:int>>).v
        return sw_obj_str_from_go_str(this.v[i : i + 1])
        !>>
    }

    public func __getslice__(bi, ei)
    {
        (bi, ei) = _make_array_real_slice_range("str", bi, ei, this.len());
        !<<
        b := l_bi.(*sw_cls_@<<:int>>).v
        e := l_ei.(*sw_cls_@<<:int>>).v
        return sw_obj_str_from_go_str(this.v[b : e])
        !>>
    }

    func _cmp_oper(op, other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            v := l_other.(*sw_cls_@<<:str>>).v
            bool result
            switch l_op.(*sw_cls_@<<:str>>).v {
            case "<":
                result = this.v < v
            case "==":
                result = this.v == v
            default:
                panic("bug")
            }
            return sw_obj_bool_from_go_bool(result)
            !>>
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

    public func hash()
    {
        //todo
        throw(NotImpl());
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
