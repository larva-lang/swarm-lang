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
        this.v = l_s.go_str()
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
        i := l_real_idx.go_int()
        return sw_obj_str_from_go_str(this.v[i : i + 1])
        !>>
    }

    public func __getslice__(bi, ei)
    {
        (bi, ei) = _make_array_real_slice_range("str", bi, ei, this.len());
        !<<
        b := l_bi.go_int()
        e := l_ei.go_int()
        return sw_obj_str_from_go_str(this.v[b : e])
        !>>
    }

    func _cmp_oper(op, other)
    {
        if (isinstanceof(other, str))
        {
            !<<
            v := l_other.go_str()
            var result bool
            switch l_op.go_str() {
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
            return sw_obj_str_from_go_str(this.v + l_other.go_str())
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
            count       := l_other.go_int()
            if count < 0 || (count > 0 && this_len * count / count != this_len) {
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
        return sw_obj{iv: int64(len(this.v))}
        !>>
    }

    public func has(s)
    {
        if (!isinstanceof(s, str))
        {
            throw(TypeError("str.has(x)的参数需要是字符串"));
        }

        !<<
        v := l_s.go_str()
        if strings.Contains(this.v, v) {
        !>>
            return 1;
        !<<
        } else {
        !>>
            return 0;
        !<<
        }
        !>>
    }

    public func hash()
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
            sl = append(sl, l_s.go_str())
            !>>
        }
        !<<
        return sw_obj_str_from_go_str(strings.Join(sl, this.v))
        !>>
    }
}

!<<

func sw_obj_str_from_go_str(s string) sw_obj {
    return sw_obj{
        ov: &sw_cls_@<<:str>>{
            v:  s,
        },
    }
}

func sw_obj_to_go_str(obj sw_obj) string {
    //直接构造str对象并返回其内部value
    return sw_new_obj_sw_cls_@<<:str>>_1(obj).go_str()
}

!>>
