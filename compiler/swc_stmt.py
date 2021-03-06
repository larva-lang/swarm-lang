#coding=utf8

import swc_util, swc_expr, swc_mod, swc_token, swc_type

class _Stmt:
    def __init__(self, type, **kw_arg):
        self.type = type
        for k, v in kw_arg.iteritems():
            setattr(self, k, v)

class Parser:
    def __init__(self, token_list, mod, cls, fom):
        self.token_list = token_list
        self.mod        = mod
        self.cls        = cls
        self.fom        = fom

        self.expr_parser    = swc_expr.Parser(token_list, mod, cls, fom, self)
        self.stmt_list_stk  = []

    def parse(self, var_map_stk, loop_deep):
        stmt_list = []
        self.stmt_list_stk.append(stmt_list)
        while True:
            if self.token_list.peek().is_sym("}"):
                self.stmt_list_stk.pop()
                return stmt_list

            t = self.token_list.pop()

            if t.is_sym(";"):
                t.warn("空语句")
                continue

            if t.is_sym("{"):
                #新代码块
                stmt_list.append(_Stmt("block", stmt_list = self.parse(var_map_stk + (swc_util.OrderedDict(),), loop_deep)))
                self.token_list.pop_sym("}")
                continue

            if t.is_reserved and t.value in ("break", "continue"):
                if loop_deep == 0:
                    t.syntax_err("循环外的%s" % t.value)
                stmt_list.append(_Stmt(t.value))
                self.token_list.pop_sym(";")
                continue

            if t.is_reserved("return"):
                if self.token_list.peek().is_sym(";"):
                    stmt = _Stmt("return_default")
                else:
                    stmt = _Stmt("return", expr = self.expr_parser.parse(var_map_stk, self.fom.tp))
                stmt_list.append(stmt)
                self.token_list.pop_sym(";")
                continue

            if t.is_reserved("for"):
                for_var_map, iter_expr = self._parse_for_prefix(var_map_stk)
                assert len(for_var_map) == 1
                self.token_list.pop_sym("{")
                for_stmt_list = self.parse(var_map_stk + (for_var_map, swc_util.OrderedDict()), loop_deep + 1)
                self.token_list.pop_sym("}")
                stmt_list.append(_Stmt("for", for_var_map = for_var_map, iter_expr = iter_expr, stmt_list = for_stmt_list))
                continue

            if t.is_reserved("while"):
                self.token_list.pop_sym("(")
                expr = self.expr_parser.parse(var_map_stk, swc_type.make_bool_type(self.token_list.peek()))
                self.token_list.pop_sym(")")
                self.token_list.pop_sym("{")
                while_stmt_list = self.parse(var_map_stk + (swc_util.OrderedDict(),), loop_deep + 1)
                self.token_list.pop_sym("}")
                stmt_list.append(_Stmt("while", expr = expr, stmt_list = while_stmt_list))
                continue

            if t.is_reserved("if"):
                if_expr_list = []
                if_stmt_list_list = []
                else_stmt_list = None
                while True:
                    self.token_list.pop_sym("(")
                    expr = self.expr_parser.parse(var_map_stk, swc_type.make_bool_type(self.token_list.peek()))
                    self.token_list.pop_sym(")")
                    self.token_list.pop_sym("{")
                    if_stmt_list = self.parse(var_map_stk + (swc_util.OrderedDict(),), loop_deep)
                    self.token_list.pop_sym("}")
                    if_expr_list.append(expr)
                    if_stmt_list_list.append(if_stmt_list)
                    if not self.token_list.peek().is_reserved("else"):
                        break
                    self.token_list.pop()
                    t = self.token_list.pop()
                    if t.is_reserved("if"):
                        continue
                    if not t.is_sym("{"):
                        t.syntax_err("需要'{'")
                    else_stmt_list = self.parse(var_map_stk + (swc_util.OrderedDict(),), loop_deep)
                    self.token_list.pop_sym("}")
                    break
                stmt_list.append(_Stmt("if", if_expr_list = if_expr_list, if_stmt_list_list = if_stmt_list_list,
                                       else_stmt_list = else_stmt_list))
                continue

            if t.is_reserved("var"):
                def parse_single_lv():
                    t, name, tp = swc_mod.parse_var_name_def(self.token_list)
                    self._add_lv(name, tp, var_map_stk)
                    if self.token_list.peek().is_sym("="):
                        self.token_list.pop_sym("=")
                        init_expr = self.expr_parser.parse(var_map_stk, None)
                        if tp.is_obj:
                            #没有指定变量类型，直接使用初始化表达式的类型
                            tp = tp.to_other_type(init_expr.tp)
                            var_map_stk[-1][name] = tp
                    else:
                        init_expr = None
                    stmt_list.append(_Stmt("var_def", name = name, tp = tp, init_expr = init_expr))
                swc_util.parse_items(self.token_list, parse_single_lv, ";")
                continue

            if t.is_reserved("defer"):
                expr = self.expr_parser.parse(var_map_stk, None)
                if expr.op not in ("call_this.method", "call_method", "call_func"):
                    t.syntax_err("defer表达式必须是一个函数或方法调用")
                self.token_list.pop_sym(";")
                stmt_list.append(_Stmt("defer", expr = expr))
                continue

            if t.is_native_code:
                stmt_list.append(_Stmt("native_code", nc = swc_mod.NativeCode(self.mod, t), fom = self.fom))
                continue

            if t.is_reserved("else"):
                t.syntax_err("未匹配if的else")

            self.token_list.revert()

            expr_token = self.token_list.peek()
            expr = self.expr_parser.parse(var_map_stk, None)
            t, sym = self.token_list.pop_sym()
            if sym == ";":
                stmt_list.append(_Stmt("expr", expr = expr))
                continue
            if sym != "=":
                t.syntax_err("需要‘;’或‘=’")

            lvalue = expr
            if not lvalue.is_lvalue:
                expr_token.syntax_err("需要左值")
            def check_final_gv(lvalue_e):
                if lvalue_e.op == "gv":
                    gv = lvalue_e.arg
                    if gv.is_final:
                        expr_token.syntax_err("不能对final修饰的全局变量‘%s’赋值" % gv)
                elif lvalue_e.op == "tuple":
                    el = lvalue_e.arg
                    assert el
                    for e in el:
                        check_final_gv(e)
            check_final_gv(lvalue)
            expr = self.expr_parser.parse(var_map_stk, lvalue.tp)
            self.token_list.pop_sym(";")
            stmt_list.append(_Stmt("assign", lvalue = lvalue, expr = expr))

    def def_func_obj(self, func_obj):
        self.stmt_list_stk[-1].append(_Stmt("def_func_obj", func_obj = func_obj))

    def _parse_for_prefix(self, var_map_stk):
        self.token_list.pop_sym("(")
        t = self.token_list.pop()
        if not t.is_reserved("var"):
            t.syntax_err("需要‘var’")
        t, name, tp = swc_mod.parse_var_name_def(self.token_list)
        for_var_map = swc_util.OrderedDict()
        self._add_lv(name, tp, var_map_stk + (for_var_map,))
        self.token_list.pop_sym(":")
        iter_expr = self.expr_parser.parse(var_map_stk, swc_type.make_obj_type(self.token_list.peek())) #iter_expr不能用for_var_map的变量
        self.token_list.pop_sym(")")
        return for_var_map, iter_expr

    def _add_lv(self, name, tp, var_map_stk):
        if name in var_map_stk[-1]:
            tp.token.syntax_err("局部变量‘%s’重定义")
        for var_map in var_map_stk[: -1]:
            if name in var_map:
                tp.token.syntax_err("局部变量‘%s’和上层局部变量名字冲突")
        swc_mod.check_lv_name_conflict(name, tp.token, self.mod)
        var_map_stk[-1][name] = tp
