#coding=utf8

import swc_util, swc_mod, swc_token, swc_type

_UNARY_OP_SET = set(["~", "!", "neg", "pos"])
_BINOCULAR_OP_SET = swc_token.BINOCULAR_OP_SYM_SET
_OP_PRIORITY_LIST = [["if", "else", "if-else"],
                     ["||"],
                     ["&&"],
                     ["|"],
                     ["^"],
                     ["&"],
                     ["===", "!==",  "==", "!="],
                     ["<", "<=", ">", ">="],
                     ["<<", ">>"],
                     ["+", "-"],
                     ["*", "/", "%"],
                     ["~", "!", "neg", "pos"]]
_OP_PRIORITY_MAP = {}
for _i in xrange(len(_OP_PRIORITY_LIST)):
    for _op in _OP_PRIORITY_LIST[_i]:
        _OP_PRIORITY_MAP[_op] = _i
del _i
del _op

class _Expr:
    def __init__(self, op, arg, tp):
        self.op     = op
        self.arg    = arg
        self.tp     = tp

        self.is_lvalue = op in ("gv", "lv", "this.attr", ".") or (op == "tuple" and arg and all([e.is_lvalue for e in arg]))

        self.pos_info = None #位置信息，只有在解析栈finish时候才会被赋值为解析栈的开始位置，参考相关代码，主要用于output时候的代码位置映射构建

class _ParseStk:
    #解析表达式时使用的栈
    def __init__(self, start_token, mod, cls, fom):
        self.start_token    = start_token
        self.mod            = mod
        self.cls            = cls
        self.fom            = fom

        self.stk    = []
        self.op_stk = []

    def _push_op(self, op):
        #弹出所有优先级高的运算
        while self.op_stk:
            if _OP_PRIORITY_MAP[self.op_stk[-1]] > _OP_PRIORITY_MAP[op]:
                self._pop_top_op()
            elif _OP_PRIORITY_MAP[self.op_stk[-1]] < _OP_PRIORITY_MAP[op]:
                break
            else:
                #同优先级看结合性
                if op in _UNARY_OP_SET:
                    #单目运算符右结合
                    break
                if op in ("if", "else"):
                    assert self.op_stk[-1] in ("if", "if-else")
                    if self.op_stk[-1] == "if" and op == "else":
                        #匹配了三目运算符，在外面统一处理合并
                        break
                    self.start_token.syntax_err("禁止多个'if-else'表达式直接混合运算，请加括号")
                self._pop_top_op()
        if op == "else":
            if self.op_stk and self.op_stk[-1] == "if":
                self.op_stk[-1] = "if-else"
                return
            self.start_token.syntax_err("非法的表达式，存在未匹配'if'的'else'")
        self.op_stk.append(op)

    def _pop_top_op(self):
        op = self.op_stk.pop()

        if op in _UNARY_OP_SET:
            #单目运算符
            if len(self.stk) < 1:
                self.start_token.syntax_err("非法的表达式")
            e = self._pop_expr()
            if (op == "!" and not e.tp.is_bool) or (op != "!" and not e.tp.is_int):
                self.start_token.syntax_err("不能对类型‘%s’做‘%s’运算" % (e.tp, op))
            self._push_expr(_Expr(op, e, e.tp))

        elif op in _BINOCULAR_OP_SET:
            #双目运算符
            if len(self.stk) < 2:
                self.start_token.syntax_err("非法的表达式")
            eb = self._pop_expr()
            ea = self._pop_expr()
            invalid_expr_syntax_err = lambda: self.start_token.syntax_err("不能对类型‘%s’和‘%s’做‘%s’运算" % (ea.tp, tb.tp, op))
            if ea.tp != eb.tp:
                invalid_expr_syntax_err()
            tp = ea.tp
            if op in ("===", "!=="):
                if not tp.is_obj:
                    invalid_expr_syntax_err()
                tp = tp.to_bool_type()
            elif op in ("&&", "||"):
                if not tp.is_bool:
                    invalid_expr_syntax_err()
            elif op in ("==", "!="):
                if tp.is_obj:
                    invalid_expr_syntax_err()
                tp = tp.to_bool_type()
            else:
                if not tp.is_int:
                    invalid_expr_syntax_err()
                if op in ("<", ">", "<=", ">="):
                    tp = tp.to_bool_type()
            self._push_expr(_Expr(op, (ea, eb), tp))

        elif op == "if":
            self.start_token.syntax_err("非法的表达式，存在未匹配'else'的'if'")

        elif op == "if-else":
            #三目运算符
            if len(self.stk) < 3:
                self.start_token.syntax_err("非法的表达式")
            eb = self._pop_expr()
            e_cond = self._pop_expr()
            ea = self._pop_expr()
            if not e_cond.tp.is_bool:
                self.start_token.syntax_err("‘if-else’表达式的条件表达式必须是bool类型")
            if ea.tp != eb.tp:
                self.start_token.syntax_err("‘if-else’表达式的两个分支运算分量类型必须相同")
            self._push_expr(_Expr(op, (e_cond, ea, eb), ea.tp))

        else:
            swc_util.abort()

    def _push_expr(self, e):
        self.stk.append(e)

    def _pop_expr(self):
        return self.stk.pop()

    def finish(self):
        while self.op_stk:
            self._pop_top_op()
        if len(self.stk) != 1:
            self.start_token.syntax_err("非法的表达式")
        e = self._pop_expr()
        e.pos_info = self.start_token, self.fom
        return e

def _is_expr_end(t):
    if t.is_sym:
        if t.value in (")", "]", ",", ";", ":", "}", "="):
            return True
    return False

class Parser:
    def __init__(self, token_list, mod, cls, fom, caller):
        self.token_list     = token_list
        self.mod            = mod
        self.cls            = cls
        self.fom            = fom
        self.caller         = caller    #使用parser的逻辑对象，有的流程中会回调其中的方法

    def parse(self, var_map_stk, need_tp):
        start_token = self.token_list.peek()
        parse_stk = _ParseStk(start_token, self.mod, self.cls, self.fom)
        while True:
            t = self.token_list.pop()

            if t.is_sym and t.value in ("~", "!", "+", "-"):
                #单目运算
                op = {
                    "+": "pos",
                    "-": "neg",
                }.get(t.value, t.value)
                parse_stk._push_op(op)
                continue

            if t.is_sym("("):
                #子表达式或tuple
                start_t = t
                if self.token_list.peek().is_sym(")"):
                    #空tuple
                    self.token_list.pop_sym(")")
                    parse_stk._push_expr(_Expr("tuple", [], swc_type.make_obj_type(start_t)))
                else:
                    e = self.parse(var_map_stk, None)
                    t = self.token_list.pop()
                    if t.is_sym(")"):
                        #子表达式
                        parse_stk._push_expr(e)
                    elif t.is_sym(","):
                        #tuple
                        el = [e] + self._parse_expr_list(var_map_stk, ")")
                        self._el_to_obj_el(el)
                        parse_stk._push_expr(_Expr("tuple", el, swc_type.make_obj_type(start_t)))
                    else:
                        t.syntax_err("需要‘,’或‘)’")

            elif t.is_sym("["):
                #list
                el = self._parse_expr_list(var_map_stk, "]")
                self._el_to_obj_el(el)
                parse_stk._push_expr(_Expr("list", el, swc_type.make_obj_type(t)))

            elif t.is_sym("{"):
                #dict
                start_t = t
                kvel = []
                while True:
                    if self.token_list.peek().is_sym("}"):
                        self.token_list.pop()
                        break
                    ek = self.parse(var_map_stk, None)
                    self.token_list.pop_sym(":")
                    ev = self.parse(var_map_stk, None)
                    kvel.append((self._to_obj_e(ek), self._to_obj_e(ev)))
                    t, sym = self.token_list.pop_sym()
                    if sym == ",":
                        continue
                    if sym == "}":
                        break
                    t.syntax_err("需要‘,’或‘}’")
                parse_stk._push_expr(_Expr("dict", kvel, swc_type.make_obj_type(start_t)))

            elif t.is_name:
                #name
                name = t.value
                if name in self.mod.dep_mod_set:
                    m = swc_mod.mod_map[name]
                    self.token_list.pop_sym(".")
                    t, name = self.token_list.pop_name()
                    e = self._parse_mod_elem_expr(m, t, name, var_map_stk)
                    parse_stk._push_expr(e)
                else:
                    for var_map in reversed(var_map_stk):
                        if name in var_map:
                            #局部变量
                            parse_stk._push_expr(_Expr("lv", name, var_map[name]))
                            break
                    else:
                        #当前模块或builtin模块的name
                        for m in self.mod, swc_mod.builtins_mod:
                            ns = m.name_set() if m is self.mod else m.public_name_set()
                            if name in ns:
                                e = self._parse_mod_elem_expr(m, t, name, var_map_stk)
                                parse_stk._push_expr(e)
                                break
                        else:
                            t.syntax_err("未定义的标识符'%s'" % name)

            elif t.is_literal:
                #literal
                if t.is_literal("bool"):
                    tp = swc_type.make_bool_type(t)
                elif t.is_literal("int"):
                    tp = swc_type.make_int_type(t)
                else:
                    tp = swc_type.make_obj_type(t)
                e = _Expr("literal", t, tp)
                if t.is_literal("str") and self.token_list.peek().is_sym(".") and self.token_list.peek(1).is_sym("("):
                    #字符串字面量的format语法
                    fmt, el = self._parse_str_format(var_map_stk, t)
                    e = _Expr("str_format", (fmt, el), tp)
                parse_stk._push_expr(e)

            elif t.is_reserved("this"):
                #this
                if self.cls is None:
                    t.syntax_err("‘this’只能用于方法中")
                parse_stk._push_expr(_Expr("this", t, swc_type.make_type_from_cls(self.cls)))

            elif t.is_reserved("func"):
                #函数对象
                func_obj = swc_mod.parse_func_obj(t, self.token_list, self.mod, self.cls, var_map_stk)
                self.caller.def_func_obj(func_obj)
                parse_stk._push_expr(_Expr("func_obj", func_obj, swc_type.make_obj_type(t)))

            elif t.is_reserved("isinstanceof"):
                tp = swc_type.make_bool_type(t)
                self.token_list.pop_sym("(")
                e = self.parse(var_map_stk, swc_type.make_obj_type(self.token_list.peek()))
                self.token_list.pop_sym(",")
                t = self.token_list.pop()
                if t.is_reserved("bool") or t.is_reserved("int"):
                    if e.op == "this":
                        assert self.cls is not None
                        parse_stk._push_expr(_Expr("isinstanceof_this", False, tp))
                    else:
                        parse_stk._push_expr(_Expr("isinstanceof_%s" % t.value, e, tp))
                else:
                    if not t.is_name:
                        t.syntax_err("需要类型")
                    name = t.value
                    if name in self.mod.dep_mod_set:
                        m = swc_mod.mod_map[name]
                        self.token_list.pop_sym(".")
                        _, name = self.token_list.pop_name()
                        cls = m.cls_map.get(name)
                        if cls is None:
                            t.syntax_err("无效的类‘%s.%s’" % (m, name))
                    else:
                        for m in self.mod, swc_mod.builtins_mod:
                            cls = m.cls_map.get(name)
                            if cls is not None:
                                break
                        else:
                            t.syntax_err("无效的类‘%s’" % name)
                    if e.op == "this":
                        #对this做判断需要特殊处理下
                        assert self.cls is not None
                        parse_stk._push_expr(_Expr("isinstanceof_this", cls is self.cls, tp))
                    else:
                        parse_stk._push_expr(_Expr("isinstanceof", (e, cls), tp))
                self.token_list.pop_sym(")")

            else:
                t.syntax_err("非法的表达式")

            assert parse_stk.stk

            #解析后缀运算符
            while True:
                t = self.token_list.pop()

                if t.is_sym("."):
                    obj_expr = parse_stk._pop_expr()
                    t = self.token_list.pop()
                    if t.is_reserved("bool") or t.is_reserved("int"):
                        #基础类型断言
                        if not obj_expr.tp.is_obj:
                            t.syntax_err("只能对对象类型的值做基础类型断言")
                        if obj_expr.op == "this":
                            t.syntax_err("不能对‘this’做基础类型断言")

                        if t.is_reserved("bool"):
                            tp = swc_type.make_bool_type(t)
                        elif t.is_reserved("int"):
                            tp = swc_type.make_int_type(t)
                        else:
                            swc_util.abort()

                        parse_stk._push_expr(_Expr("type_assert_%s" % t.value, obj_expr, tp))
                        continue

                    #属性或方法调用
                    if not t.is_name:
                        t.syntax_err("需要标识符")
                    name = t.value
                    if self.token_list.peek().is_sym("("):
                        #方法调用
                        self.token_list.pop_sym("(")
                        el = self._parse_expr_list(var_map_stk, ")")
                        arg_count = len(el)
                        if obj_expr.op == "this":
                            method = self.cls.method_map.get(name)
                            if method is None:
                                t.syntax_err("类‘%s’没有方法‘%s’" % (self.cls, name))
                            self._check_arg_list(t, method.arg_map, el)
                            parse_stk._push_expr(_Expr("call_this.method", (name, el), method.tp))
                        else:
                            if name != "call":
                                ms = (name, arg_count)
                                if ms not in swc_mod.all_usr_method_sign_set and ms not in swc_mod.internal_method_sign_set:
                                    #尽量检测一下，可能漏报错误，但保证了目标代码不会编译失败
                                    t.syntax_err("程序中没有签名为‘%s<%d>’的方法" % (name, arg_count))
                            self._el_to_obj_el(el)
                            parse_stk._push_expr(_Expr("call_method", (obj_expr, name, el), swc_type.make_obj_type(t)))
                    else:
                        #属性访问
                        if obj_expr.op == "this":
                            attr = self.cls.attr_map.get(name)
                            if attr is None:
                                t.syntax_err("类‘%s’没有属性‘%s’" % (self.cls, name))
                            parse_stk._push_expr(_Expr("this.attr", name, attr.tp))
                        else:
                            if name not in swc_mod.all_attr_name_set:
                                t.syntax_err("程序中没有名为‘%s’的属性" % name)
                            parse_stk._push_expr(_Expr(".", (obj_expr, name), swc_type.make_obj_type(t)))

                else:
                    self.token_list.revert()
                    break

            if _is_expr_end(self.token_list.peek()):
                #表达式结束
                break

            #状态：解析普通双、三目运算符
            t = self.token_list.pop()
            if (t.is_sym and t.value in _BINOCULAR_OP_SET) or (t.is_reserved and t.value in ("if", "else")):
                #双、三目运算
                parse_stk._push_op(t.value)
            else:
                t.syntax_err("需要双目或三目运算符")

        e = parse_stk.finish()
        if need_tp is not None:
            if need_tp != e.tp:
                parse_stk.start_token.syntax_err("表达式需要是‘%s’类型" % need_tp)
        return e

    def _check_arg_list(self, t, arg_map, el):
        if len(arg_map) != len(el):
            t.syntax_err("参数数量不匹配，需要%d个" % len(arg_map))
        for i, (arg_tp, e) in enumerate(zip(arg_map.itervalues(), el)):
            if arg_tp != e.tp:
                t.syntax_err("参数#%d类型不匹配" % (i + 1))

    def _to_obj_e(self, e):
        if e.tp.is_bool:
            e = _Expr("bool_to_obj", e, e.tp.to_obj_type())
        elif e.tp.is_int:
            e = _Expr("int_to_obj", e, e.tp.to_obj_type())
        else:
            pass
        return e

    def _el_to_obj_el(self, el):
        for i, e in enumerate(el):
            el[i] = self._to_obj_e(e)

    def _parse_mod_elem_expr(self, mod, name_token, name, var_map_stk):
        elem = mod.get_elem(name)
        if elem is None:
            name_token.syntax_err("找不到‘%s.%s’" % (mod, name))

        if not (elem.is_public or self.mod is mod):
            name_token.syntax_err("无法访问‘%s’，没有权限" % elem)

        if elem.is_gv:
            return _Expr("gv", elem, elem.tp)

        if elem.is_cls or elem.is_func:
            #类和函数的使用都是直接调用
            self.token_list.pop_sym("(")
            el_start_token = self.token_list.peek()
            el = self._parse_expr_list(var_map_stk, ")")

            if elem.is_cls:
                #调用的是类的构造函数，获取其参数表
                construct_method = elem.get_construct_method()
                if construct_method is None:
                    name_token.syntax_err("无法创建‘%s’的实例，没有构造方法" % elem)
                if not (construct_method.is_public or self.mod is mod):
                    name_token.syntax_err("无法创建‘%s’的实例，对构造方法没有权限" % elem)
                self._check_arg_list(name_token, construct_method.arg_map, el)
                op = "new_obj"
                tp = swc_type.make_type_from_cls(elem)
            elif elem.is_func:
                self._check_arg_list(name_token, elem.arg_map, el)
                op = "call_func"
                tp = elem.tp
            else:
                swc_util.abort()

            return _Expr(op, (elem, el), tp)

        swc_util.abort()

    def _parse_expr_list(self, var_map_stk, end_sym):
        el = []
        if self.token_list.peek().is_sym(end_sym):
            self.token_list.pop()
        else:
            def parse_single_expr():
                el.append(self.parse(var_map_stk, None))
            swc_util.parse_items(self.token_list, parse_single_expr, end_sym)
        return el

    def _parse_str_format(self, var_map_stk, t):
        assert t.is_literal("str")
        self.token_list.pop_sym(".")
        self.token_list.pop_sym("(")
        el = self._parse_expr_list(var_map_stk, ")")
        fmt = ""
        pos = 0
        ei = 0
        while pos < len(t.value):
            if t.value[pos] != "%":
                fmt += t.value[pos]
                pos += 1
                continue
            class FmtIdxErr(Exception):
                pass
            def fmt_chr():
                if pos < len(t.value):
                    return t.value[pos]
                raise FmtIdxErr()
            try:
                pos += 1
                if fmt_chr() == "%":
                    fmt += "%%"
                    pos += 1
                    continue
                if ei >= len(el):
                    t.syntax_err("format格式化参数不足")
                expr = el[ei]
                #解析格式字符
                verb = fmt_chr()
                pos += 1
                if verb in "sT":
                    #合法格式
                    el[ei] = _Expr("to_go_fmt_str", (verb, expr), None)
                else:
                    t.syntax_err("非法的格式符：'%s...'" % `t.value[: pos]`[1 : -1])
                fmt += "%s"
                ei += 1
            except FmtIdxErr:
                t.syntax_err("format格式串非正常结束")
        if ei < len(el):
            t.syntax_err("format格式化参数过多")
        return fmt, el
