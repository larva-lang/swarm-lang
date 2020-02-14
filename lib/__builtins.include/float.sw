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
            s := l_x.(*sw_cls_@<<:str>>).v
            v, err := strconv.ParseFloat(s, 64)
            if err != nil {
            !>>
                throw(ValueError("字符串‘%s’不能转为float对象".(x)));
            !<<
            }
            this.v = v
            !>>
            return;
        }

        if (isinstanceof(x, float))
        {
            !<<
            this.v = l_x.(*sw_cls_@<<:float>>).v
            !>>
            return;
        }

        if (isinstanceof(x, int))
        {
            !<<
            this.v = float64(l_x.(*sw_cls_@<<:int>>).v)
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
        return this != 0.0;
    }

    public func __lt__(other)
    {
        !<<
        if v, ok := sw_obj_number_to_go_float(l_other); ok {
            return sw_obj_bool_from_go_bool(this.v < v)
        }
        !>>
        throw_unsupported_binocular_oper("<", this, other);
    }

    public func __eq__(other)
    {
        !<<
        if v, ok := sw_obj_number_to_go_float(l_other); ok {
            return sw_obj_bool_from_go_bool(this.v == v)
        }
        !>>
        throw_unsupported_binocular_oper("==", this, other);
    }

    func _arithmetic_binocular_oper(op, other)
    {
        !<<
        if v, ok := sw_obj_number_to_go_float(l_other); ok {
            var result float64
            switch l_op.(*sw_cls_@<<:str>>).v {
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

func sw_obj_float_from_go_float(f float64) *sw_cls_@<<:float>> {
    return &sw_cls_@<<:float>>{
        v:  f,
    }
}

func sw_obj_number_to_go_float(x sw_obj) (v float64, ok bool) {
    switch o := x.(type) {
    case *sw_cls_@<<:int>>:
        return float64(o.v), true
    case *sw_cls_@<<:float>>:
        return o.v, true
    default:
        return 0, false
    }
}

!>>
