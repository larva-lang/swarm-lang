public class int
{
    !<<
    v   int64
    !>>

    public func __init__(x)
    {
        if (isinstanceof(x, str))
        {
            !<<
            s := l_x.(*sw_cls_@<<:str>>).v
            v, err := strconv.ParseInt(s, 0, 64)
            if err != nil {
            !>>
                throw(ValueError("无效的int的字符串表示：‘%s’".(x)));
            !<<
            }
            this.v = v
            !>>
            return;
        }

        if (isinstanceof(x, float))
        {
            !<<
            this.v = int64(l_x.(*sw_cls_@<<:float>>).v)
            !>>
            return;
        }

        if (isinstanceof(x, int))
        {
            !<<
            this.v = l_x.(*sw_cls_@<<:int>>).v
            !>>
            return;
        }

        throw(TypeError("不支持类型‘%T’到int的转换".(x)));
    }

    public func __init__(x, base)
    {
        if (isinstanceof(x, str) && isinstanceof(base, int))
        {
            if (base < 0 || base == 1 || base > 36)
            {
                throw(ValueError("不支持%d进制".(base)));
            }
            !<<
            s := l_x.(*sw_cls_@<<:str>>).v
            b := l_base.(*sw_cls_@<<:int>>).v
            v, err := strconv.ParseInt(s, int(b), 64)
            if err != nil {
            !>>
                throw(ValueError("无效的%sint的字符串表示：‘%s’".("" if base == 0 else "%d进制".(base), x)));
            !<<
            }
            this.v = v
            !>>
            return;
        }

        throw(TypeError("int(x, base)的参数类型需要是‘str’和‘int’"));
    }

    public func __repr__()
    {
        return "%d".(this);
    }

    public func __bool__()
    {
        return this != 0;
    }

    func _cmp_oper(op, other)
    {
        if (isinstanceof(other, int))
        {
            !<<
            v := l_other.(*sw_cls_@<<:int>>).v
            bool result;
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

        if (isinstanceof(other, float))
        {
            var f = float(this);
            if (op == "<")
            {
                return f < other;
            }
            if (op == "==")
            {
                return f == other;
            }
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

    func _arithmetic_binocular_oper(op, other)
    {
        if (isinstanceof(other, int))
        {
            if ("/、%".has(op) && other == 0)
            {
                throw(DivByZeroError());
            }
            if ("<<、>>".has(op) && other < 0)
            {
                throw(ShiftByNegError());
            }
            !<<
            v := l_other.(*sw_cls_@<<:int>>).v
            var result int64
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
                result = this.v % v
            case "<<":
                result = this.v << uint64(v)
            case ">>":
                result = this.v >> uint64(v)
            case "&":
                result = this.v & v
            case "|":
                result = this.v | v
            case "^":
                result = this.v ^ v
            default:
                panic("bug")
            }
            return sw_obj_int_from_go_int(result)
            !>>
        }

        if (isinstanceof(other, float) && "+、-、*、/、%".has(op))
        {
            return float(this)._arithmetic_binocular_oper(op, other);
        }

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
    public func __shl__(other)
    {
        return this._arithmetic_binocular_oper("<<", other);
    }
    public func __shr__(other)
    {
        return this._arithmetic_binocular_oper(">>", other);
    }
    public func __and__(other)
    {
        return this._arithmetic_binocular_oper("&", other);
    }
    public func __or__(other)
    {
        return this._arithmetic_binocular_oper("|", other);
    }
    public func __xor__(other)
    {
        return this._arithmetic_binocular_oper("^", other);
    }

    public func __inv__()
    {
        !<<
        return sw_obj_int_from_go_int(^this.v)
        !>>
    }

    public func __pos__()
    {
        return this;
    }

    public func __neg__()
    {
        !<<
        return sw_obj_int_from_go_int(-this.v)
        !>>
    }
}

!<<

func sw_obj_int_from_go_int(i int64) *sw_cls_@<<:int>> {
    return &sw_cls_@<<:int>>{
        v:  i,
    }
}

!>>
