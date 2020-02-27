//用于双目运算不支持时的异常抛出，简化开发
public func throw_unsupported_binocular_oper(op, a, b)
{
    throw(TypeError("不支持类型‘%T’和‘%T’的‘%s’运算".(a, b, op)));
}
