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
            s := sw_obj_str_to_go_str(l_x)
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
            this.v = l_x.(*sw_cls_@<<:float>>).v
            !>>
            return;
        }

        if (isinstanceof(x, int))
        {
            !<<
            this.v = float64(l_x.(sw_cls_int))
            !>>
            return;
        }

        throw(TypeError("不支持类型‘%T’到float的转换".(x)));
    }

    public func __repr__()
    {
        !<<
        return sw_obj_str_from_go_str(fmt.Sprintf("%g", this.v))
        !>>
    }

    public func cmp(other) int
    {
        if (isinstanceof(other, float))
        {
            !<<
            other_v := l_other.(*sw_cls_@<<:float>>).v
            if this.v < other_v {
                return -1
            } else if this.v > other_v {
                return 1
            } else {
                return 0
            }
            !>>
        }
        throw_unsupported_binocular_oper("比较", this, other);
    }

    public func eq(other) int
    {
        return this.cmp(other) == 0;
    }

    func _arithmetic_binocular_oper(op, other)
    {
        !<<
        if v, ok := l_other.(*sw_cls_@<<:float>>).v; ok {
            var result float64
            switch sw_obj_str_to_go_str(l_op) {
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

    public func add(other)
    {
        return this._arithmetic_binocular_oper("+", other);
    }
    public func sub(other)
    {
        return this._arithmetic_binocular_oper("-", other);
    }
    public func mul(other)
    {
        return this._arithmetic_binocular_oper("*", other);
    }
    public func div(other)
    {
        return this._arithmetic_binocular_oper("/", other);
    }
    public func mod(other)
    {
        return this._arithmetic_binocular_oper("%", other);
    }

    public func neg()
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

!>>
