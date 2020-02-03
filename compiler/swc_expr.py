#coding=utf8

import swc_util, swc_mod, swc_token

class _VarDef:
    def __init__(self, vd, mod):
        self.vd     = vd
        self.mod    = mod

    def iter_names(self):
        def iter_vd(vd):
            if isinstance(vd, tuple):
                yield vd
                return
            assert isinstance(vd, list)
            for sub_vd in vd:
                for t, name in iter_vd(sub_vd):
                    yield t, name

        return iter_vd(self.vd)

def parse_var_def(token_list, mod = None):
    def parse_vd():
        t = token_list.pop()
        if t.is_name:
            return t, t.value
        if not t.is_sym("("):
            t.syntax_err("需要变量定义")
        vd = []
        while True:
            vd.append(parse_vd())
            t, sym = token_list.pop_sym()
            if sym == ")":
                if len(vd) == 1:
                    t.syntax_err("单个变量定义不能加括号，或需要‘,’")
                break
            if sym != ",":
                t.syntax_err("需要‘,’或‘)’")
            if token_list.peek().is_sym(")"):
                token_list.pop()
                break
        return vd

    return _VarDef(parse_vd(), mod)

_UNARY_OP_SET = set(["~", "!", "neg", "pos"])
_BINOCULAR_OP_SET = swc_token.BINOCULAR_OP_SYM_SET | set(["is"])
_OP_PRIORITY_LIST = [["if", "else", "if-else"],
                     ["||"],
                     ["&&"],
                     ["|"],
                     ["^"],
                     ["&"],
                     ["is", "==", "!="],
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
    def __init__(self, op, arg):
        self.op     = op
        self.arg    = arg

        self.is_lvalue = op in ("gv", "lv", "[]", ".") or (op == "tuple" and all([elem.is_lvalue for elem in arg]))

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
                        #匹配了三元运算符，在外面统一处理合并
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
            self._push_expr(_Expr(op, self._pop_expr()))

        elif op in _BINOCULAR_OP_SET:
            #双目运算符
            if len(self.stk) < 2:
                self.start_token.syntax_err("非法的表达式")
            eb = self._pop_expr()
            ea = self._pop_expr()
            self._push_expr(_Expr(op, (ea, eb)))

        elif op == "if":
            self.start_token.syntax_err("非法的表达式，存在未匹配'else'的'if'")

        elif op == "if-else":
            #三元运算符
            if len(self.stk) < 3:
                self.start_token.syntax_err("非法的表达式")
            eb = self._pop_expr()
            e_cond = self._pop_expr()
            ea = self._pop_expr()
            self._push_expr(_Expr(op, (e_cond, ea, eb)))

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
        if t.value in (set([")", "]", ",", ";", ":", "}"]) | swc_token.ASSIGN_SYM_SET):
            return True
    return False

class Parser:
    def __init__(self, token_list, mod, cls, fom, stmt_parser):
        self.token_list     = token_list
        self.mod            = mod
        self.cls            = cls
        self.fom            = fom
        self.stmt_parser    = stmt_parser

    def parse(self, var_map_stk):
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
                e = self.parse(var_map_stk)
                t = self.token_list.pop()
                if t.is_sym(")"):
                    #子表达式
                    parse_stk._push_expr(e)
                elif t.is_sym(","):
                    #tuple
                    el = [e] + self._parse_expr_list(var_map_stk, ")")
                    parse_stk._push_expr(_Expr("tuple", el))
                else:
                    t.syntax_err("需要‘,’或‘)’")

            elif t.is_sym("["):
                #list
                el = self._parse_expr_list(var_map_stk, "]")
                parse_stk._push_expr(_Expr("list", el))

            elif t.is_sym("{"):
                #dict
                kvel = []
                while True:
                    if self.token_list.peek().is_sym("}"):
                        self.token_list.pop()
                        break
                    ek = self.parse(var_map_stk)
                    self.token_list.pop_sym(":")
                    ev = self.parse(var_map_stk)
                    kvel.append((ek, ev))
                    t, sym = self.token_list.pop_sym()
                    if sym == ",":
                        continue
                    if sym == "}":
                        break
                    t.syntax_err("需要‘,’或‘}’")
                parse_stk._push_expr(_Expr("dict", kvel))

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
                            parse_stk._push_expr(_Expr("lv", name))
                            break
                    else:
                        #当前模块或builtin模块的name
                        for m in self.mod, swc_mod.builtins_mod:
                            ns = m.public_name_set() if m is swc_mod.builtins_mod else m.name_set()
                            if name in ns:
                                e = self._parse_mod_elem_expr(m, t, name, var_map_stk)
                                parse_stk._push_expr(e)
                                break
                        else:
                            t.syntax_err("未定义的标识符'%s'" % name)

            elif t.is_literal:
                #literal
                e = _Expr("literal", t)
                if t.is_literal("str") and self.token_list.peek().is_sym(".") and self.token_list.peek(1).is_sym("("):
                    #字符串字面量的format语法
                    fmt, el = self._parse_str_format(var_map_stk, t)
                    e = _Expr("str_format", (fmt, el))
                parse_stk._push_expr(e)

            elif t.is_reserved("this"):
                #this
                if self.cls is None:
                    t.syntax_err("‘this’只能用于方法中")
                parse_stk._push_expr(_Expr("this", t))

            elif t.is_reserved("func"):
                #函数对象
                func_obj = swc_mod.parse_func_obj(t, self.token_list, self.mod, self.cls, var_map_stk)
                self.stmt_parser.def_func_obj(func_obj)
                parse_stk._push_expr(_Expr("func_obj", func_obj))

            else:
                t.syntax_err("非法的表达式")

            assert parse_stk.stk

            #解析后缀运算符
            while True:
                t = self.token_list.pop()

                if t.is_sym("["):
                    is_slice = False
                    if self.token_list.peek().is_sym(":"):
                        expr = None
                        is_slice = True
                    else:
                        expr = self.parse(var_map_stk)
                    if self.token_list.peek().is_sym(":"):
                        self.token_list.pop_sym(":")
                        if self.token_list.peek().is_sym("]"):
                            slice_end_expr = None
                        else:
                            slice_end_expr = self.parse(var_map_stk)
                        is_slice = True
                    self.token_list.pop_sym("]")
                    obj_expr = parse_stk._pop_expr()
                    if is_slice:
                        parse_stk._push_expr(_Expr("[:]", (obj_expr, expr, slice_end_expr)))
                    else:
                        parse_stk._push_expr(_Expr("[]", (obj_expr, expr)))

                elif t.is_sym("."):
                    t, name = self.token_list.pop_name()
                    obj_expr = parse_stk._pop_expr()
                    if self.token_list.peek().is_sym("("):
                        #方法调用
                        self.token_list.pop_sym("(")
                        el = self._parse_expr_list(var_map_stk, ")")
                        parse_stk._push_expr(_Expr("call_method", (obj_expr, name, el)))
                    else:
                        #属性访问
                        parse_stk._push_expr(_Expr(".", (obj_expr, name)))

                else:
                    self.token_list.revert()
                    break

            if _is_expr_end(self.token_list.peek()):
                #表达式结束
                break

            #状态：解析普通二元运算符
            t = self.token_list.pop()
            if (t.is_sym and t.value in _BINOCULAR_OP_SET) or (t.is_reserved and t.value in ("if", "else", "is")):
                #二、三元运算
                parse_stk._push_op(t.value)
            else:
                t.syntax_err("需要二元或三元运算符")

        return parse_stk.finish()

    def _parse_mod_elem_expr(self, mod, name_token, name, var_map_stk):
        elem = mod.get_elem(name)
        if elem is None:
            name_token.syntax_err("找不到‘%s.%s’" % (mod, name))

        if not (elem.is_public or self.mod is mod):
            name_token.syntax_err("无法访问‘%s.%s’，没有权限" % (mod, name))

        if elem.is_cls or elem.is_func:
            #类和函数的使用都是直接调用
            self.token_list.pop_sym("(")
            el_start_token = self.token_list.peek()
            el = self._parse_expr_list(var_map_stk, ")")

            if elem.is_cls:
                #调用的是类的构造函数，获取其参数表
                construct_method = elem.get_construct_method()
                if construct_method is None:
                    construct_method_is_public = False
                    arg_map = swc_util.OrderedDict()
                else:
                    construct_method_is_public = construct_method.is_public
                    arg_map = construct_method.arg_map
                if not (construct_method_is_public or self.mod is mod):
                    name_token.syntax_err("无法创建‘%s.%s’的实例，对构造方法没有权限" % (mod, name))
                op = "new_obj"
            elif elem.is_func:
                arg_map = elem.arg_map
                op = "call_func"
            else:
                swc_util.abort()

            if len(el) != len(arg_map):
                el_start_token.syntax_err("参数数量错误，需要%d个" % len(arg_map))

            return _Expr(op, (elem, el))

        if elem.is_gv:
            return _Expr("gv", elem)

        swc_util.abort()

    def _parse_expr_list(self, var_map_stk, end_sym):
        el = []
        while True:
            if self.token_list.peek().is_sym(end_sym):
                self.token_list.pop()
                break
            e = self.parse(var_map_stk)
            el.append(e)
            t, sym = self.token_list.pop_sym()
            if sym == ",":
                continue
            if sym == end_sym:
                break
            t.syntax_err("需要‘,’或‘%s’" % end_sym)
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
                if verb in "tbcdoxXeEfFgGrsT":
                    #合法格式
                    el[ei] = _Expr("to_go_fmt_str", (verb, expr))
                else:
                    t.syntax_err("非法的格式符：'%s...'" % `t.value[: pos]`[1 : -1])
                fmt += verb
                ei += 1
            except FmtIdxErr:
                t.syntax_err("format格式串非正常结束")
        if ei < len(el):
            t.syntax_err("format格式化参数过多")
        return fmt, el