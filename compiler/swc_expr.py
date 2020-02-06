#coding=utf8

import swc_util, swc_mod

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

        self.is_lvalue  = op in ("gv", "lv", "[]", ".")
        self.pos_info   = None #位置信息，只有在解析栈finish时候才会被赋值为解析栈的开始位置，参考相关代码，主要用于output时候的代码位置映射构建

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
            self.stk.append(_Expr(op, self.stk.pop()))

        elif op in _BINOCULAR_OP_SET:
            #双目运算符
            if len(self.stk) < 2:
                self.start_token.syntax_err("非法的表达式")
            eb = self.stk.pop()
            ea = self.stk.pop()
            self.stk.append(_Expr(op, (ea, eb)))

        elif op == "if":
            self.start_token.syntax_err("非法的表达式，存在未匹配'else'的'if'")

        elif op == "if-else":
            #三元运算符
            if len(self.stk) < 3:
                self.start_token.syntax_err("非法的表达式")
            eb = self.stk.pop()
            e_cond = self.stk.pop()
            ea = self.stk.pop()
            self.stk.append(_Expr(op, (e_cond, ea, eb)))

        else:
            raise Exception("Bug")

    def push_expr(self, e):
        self.stk.append(e)

    def finish(self):
        while self.op_stk:
            self._pop_top_op()
        if len(self.stk) != 1:
            self.start_token.syntax_err("非法的表达式")
        e = self.stk.pop()
        e.pos_info = self.start_token, self.fom
        return e

def _is_expr_end(t):
    if t.is_sym:
        if t.value in (set([")", "]", ",", ";", ":", "}"]) | swc_token.ASSIGN_SYM_SET):
            return True
    return False

class Parser:
    def __init__(self, token_list, mod, cls, fom):
        self.token_list = token_list
        self.mod        = mod
        self.cls        = cls
        self.fom        = fom

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
                parse_stk.push_op(op)
                continue

            if t.is_sym("("):
                #子表达式或tuple
                e = self.parse(var_map_stk)
                t = self.token_list.pop()
                if t.is_sym(")"):
                    #子表达式
                    parse_stk.push_expr(e)
                elif t.is_sym(","):
                    #tuple
                    el = [e]
                    while True:
                        if self.token_list.peek().is_sym(")"):
                            self.token_list.pop()
                            break
                        e = self.parse(var_map_stk)
                        el.append(e)
                        t, sym = self.token_list.pop_sym()
                        if sym == ",":
                            continue
                        if sym == ")":
                            break
                        t.syntax_err("需要‘,’或‘)’")
                    parse_stk.push_expr(_Expr("tuple", el))
                else:
                    t.syntax_err("需要‘,’或‘)’")

            elif t.is_sym("["):
                #list
                el = []
                while True:
                    if self.token_list.peek().is_sym("]"):
                        self.token_list.pop()
                        break
                    e = self.parse(var_map_stk)
                    el.append(e)
                    t, sym = self.token_list.pop_sym()
                    if sym == ",":
                        continue
                    if sym == "]":
                        break
                    t.syntax_err("需要‘,’或‘]’")
                parse_stk.push_expr(_Expr("list", el))

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
                parse_stk.push_expr(_Expr("dict", kvel))

            elif t.is_name:
                #name
                name = t.value
                if name in self.mod.dep_mod_set:
                    m = swc_mod.mod_map[name]
                    self.token_list.pop_sym(".")
                    t, name = self.token_list.pop_name()
                    e = self._parse_mod_elem_expr(m, t, name, var_map_stk)
                    parse_stk.push_expr(e)
                else:
                    for var_map in reversed(var_map_stk):
                        if name in var_map:
                            #局部变量
                            parse_stk.push_expr(_Expr("lv", name))
                            break
                    else:
                        #当前模块或builtin模块的name
                        for ns in self.mod.name_set(), swc_mod.builtins_mod.public_name_set():
                            if name in ns:
                                e = self._parse_mod_elem_expr(m, t, name, var_map_stk)
                                parse_stk.push_expr(e)
                                break
                        else:
                            t.syntax_err("未定义的标识符'%s'" % name)

            elif t.is_literal:
                #literal
                parse_stk.push_expr(_Expr("literal", t))

            elif t.is_reserved("this"):
                #this
                if self.cls is None:
                    t.syntax_err("‘this’只能用于方法中")
                parse_stk.push_expr(_Expr("this", t))

            elif t.is_reserved("func"):
                #函数
                todo

            else:
                t.syntax_err("非法的表达式")

            assert parse_stk.stk

            #解析后缀运算符
            while True:
                t = self.token_list.pop()

                if t.is_sym("["):
                    todo

                elif t.is_sym("."):
                    todo

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
                parse_stk.push_op(t.value)
            else:
                t.syntax_err("需要二元或三元运算符")

        return parse_stk.finish()

    def _parse_mod_elem_expr(self, mod, name_token, name, var_map_stk):
        todo
