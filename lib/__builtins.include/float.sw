public class float
{
    !<<
    v   float64
    !>>

    public func __init__(x)
    {
        if (isinstanceof(x, str))
        {
            !<<
            s := l_x.go_str()
            v, err := strconv.ParseFloat(s, 64)
            if err != nil {
            !>>
                throw(ValueError("无效的float的字符串表示：‘%s’".(x)));
            !<<
            }
            this.v = v
            !>>
            return;
        }

        if (isinstanceof(x, float))
        {
            !<<
            this.v = l_x.ov.(*sw_cls_@<<:float>>).v
            !>>
            return;
        }

        if (isinstanceof(x, int))
        {
            !<<
            this.v = float64(l_x.go_int())
            !>>
            return;
        }

        throw(TypeError("不支持类型‘%T’到float的转换".(x)));
    }

    public func __repr__()
    {
        return "%g".(this);
    }

    public func __bool__()
    {
        //todo
        throw(NotImpl());
    }

    func _cmp_oper(op, other)
    {
        !<<
        if v, ok := sw_obj_number_to_go_float(l_other); ok {
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
        }
        !>>
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

    func _arithmetic_binocular_oper(op, other)
    {
        !<<
        if v, ok := sw_obj_number_to_go_float(l_other); ok {
            var result float64
            switch l_op.go_str() {
            case "+":
                result = this.v + v
            case "-":
                result = this.v - v
            case "*":
                result = this.v * v
            case "/":
                result = this.v / v
            case "%":
                result = math.Mod(this.v, v)
            default:
                panic("bug")
            }
            return sw_obj_float_from_go_float(result)
        }
        !>>
        throw_unsupported_binocular_oper(op, this, other);
    }

    public func __add__(other)
    {
        return this._arithmetic_binocular_oper("+", other);
    }
    public func __sub__(other)
    {
        return this._arithmetic_binocular_oper("-", other);
    }
    public func __mul__(other)
    {
        return this._arithmetic_binocular_oper("*", other);
    }
    public func __div__(other)
    {
        return this._arithmetic_binocular_oper("/", other);
    }
    public func __mod__(other)
    {
        return this._arithmetic_binocular_oper("%", other);
    }

    public func __pos__()
    {
        return this;
    }

    public func __neg__()
    {
        !<<
        return sw_obj_float_from_go_float(-this.v)
        !>>
    }
}

!<<

func sw_obj_float_from_go_float(f float64) sw_obj {
    return sw_obj{
        ov: &sw_cls_@<<:float>>{
            v:  f,
        },
    }
}

func sw_obj_number_to_go_float(x sw_obj) (v float64, ok bool) {
    switch o := x.ov.(type) {
    case nil:
        return float64(x.iv), true
    case *sw_cls_@<<:float>>:
        return o.v, true
    default:
        return 0, false
    }
}

!>>
