#coding=utf8

import shutil, os, subprocess, platform, time

import swc_util, swc_mod

out_dir = None

_out_prog_dir = _prog_pkg_name = _exe_file = _main_pkg_file = _all_method_name_set = None

_POS_INFO_IGNORE = object()

_SUPER_PERM = "-19840427"   #特殊情况下需要操作属性或方法的超级权限，即无视是否public，这个功能留着暂不开启

_tb_map = {}

class _Code:
    class _CodeBlk:
        def __init__(self, code, end_line):
            self.code = code
            self.end_line = end_line

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if exc_type is not None:
                return
            assert len(self.code.indent) >= 4
            self.code.indent = self.code.indent[: -4]
            self.code += self.end_line

    class _NativeCode:
        def __init__(self, code):
            self.code = code

        def __enter__(self):
            self.code += "//native_code start"
            self.save_indent = self.code.indent
            self.code.indent = ""
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if exc_type is not None:
                return
            self.code.indent = self.save_indent
            self.code += "//native_code end"

    def __init__(self, file_path_name, pkg_name = None):
        assert file_path_name.endswith(".go")
        self.file_path_name = file_path_name
        self.line_list      = []
        self.indent         = ""

        self += "package %s" % (_prog_pkg_name if pkg_name is None else pkg_name)

    def __iadd__(self, line):
        self.line_list.append(self.indent + line)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            return

        f = open(self.file_path_name, "w")
        for line in self.line_list:
            print >> f, line
        f.close()

    def new_blk(self, title, start_with_blank_line = True, tail = ""):
        if start_with_blank_line:
            self += ""
        end_line = "}" + tail
        if title == "import":
            self += title + " ("
            end_line = ")"
        elif title == "else" or title.startswith("else if "):
            if start_with_blank_line:
                del self.line_list[-1]
            assert self.line_list[-1] == self.indent + "}"
            del self.line_list[-1]
            self += "} " + title + " {"
        elif title:
            self += title + " {"
        else:
            self += "{"
        self.indent += " " * 4
        return self._CodeBlk(self, end_line)

    def new_native_code(self):
        return self._NativeCode(self)

    #记录tb映射的信息，本code当前位置到输入的pos信息，在输出代码之前使用，adjust为代码行数修正值
    def record_tb_info(self, pos_info, adjust = 0):
        if pos_info is _POS_INFO_IGNORE:
            tb_info = None
        else:
            t, fom = pos_info
            if fom is None:
                fom = "<module>"
            tb_info = t.src_fn, t.line_idx + 1, str(fom)
        _tb_map[(self.file_path_name, len(self.line_list) + 1 + adjust)] = tb_info

def _init_all_method_name_set():
    #将所有可能的sw_method_*整合出来，不包括内部使用的类似type_name之类的

    global _all_method_name_set
    _all_method_name_set = swc_util.OrderedSet()

    #内部方法
    for name, _ in swc_mod.internal_method_sign_set:
        _all_method_name_set.add(name)

    #用户定义方法
    for name, _ in swc_mod.all_usr_method_sign_set:
        _all_method_name_set.add(name)

    #函数对象的call方法
    _all_method_name_set.add("call")

def _get_builtins_elem(name):
    return swc_mod.builtins_mod.get_elem(name)

#gens-------------------------------------------------------------

def _gen_mod_name(mod):
    return "%d_%s" % (len(mod.name), mod.name)

def _gen_init_mod_func_name(mod):
    return "sw_env_init_mod_" + _gen_mod_name(mod)

def _gen_mod_elem_name(elem):
    for i in "cls", "func", "gv":
        if eval("elem.is_%s" % i):
            return "sw_%s_%s_%d_%s" % (i, _gen_mod_name(elem.mod), len(elem.name), elem.name)

def _gen_builtins_elem_name(name):
    return _gen_mod_elem_name(_get_builtins_elem(name))

def _gen_str_literal(s):
    code_list = []
    for c in s:
        asc = ord(c)
        assert 0 <= asc <= 0xFF
        if asc < 32 or asc > 126 or c in ('"', "\\"):
            code_list.append("\\%03o" % asc)
        else:
            code_list.append(c)
    return '"%s"' % "".join(code_list)

def _gen_method_name(name):
    return "sw_method_%s" % name

def _gen_method_impl_name(name):
    return "sw_methodimpl_%s" % name

def _gen_get_attr_method_name(name):
    return "sw_attr_%s" % name

def _gen_set_attr_method_name(name):
    return "sw_setattr_%s" % name

def _gen_literal_name(t):
    return "sw_literal_%d" % t.id

def _gen_arg_def(arg_map, need_perm_arg = False):
    al = ["l_%s %s" % (name, "int64" if tp.is_int else "sw_obj") for name, tp in arg_map.iteritems()]
    if need_perm_arg:
        al = ["perm int64"] + al
    return ", ".join(al)

def _gen_new_obj_func_name(cls):
    return "sw_new_obj_%s" % _gen_mod_elem_name(cls)

def _gen_panic_str(s):
    return "panic(%s)" % _gen_str_literal(s)

def _gen_panic_bug():
    return _gen_panic_str("bug")

def _gen_throw_exc(exc):
    return "%s(%s)" % (_gen_mod_elem_name(_get_builtins_func("throw", 1)), exc)

def _gen_tmp_var_name():
    return "sw_tmp_var_%d" % swc_util.new_id()

def _gen_fo_name(fo):
    return "sw_fo_%d" % fo.id

def _gen_cls_type_name(cls):
    name = str(cls)
    builtins_prefix = "__builtins."
    if name.startswith(builtins_prefix):
        name = name[len(builtins_prefix) :]
    assert name
    return name

def _gen_type_assert_int(expr_code):
    return "int64((%s).(sw_cls_int))" % expr_code

def _gen_tp(tp):
    return "int64" if tp.is_int else "sw_obj"

#gens end-------------------------------------------------------------

_curr_mod = None

_UNARY_OP_2_INTERNAL_METHOD = {
    "~":    "inv",
    "neg":  "neg",
    "pos":  "pos",
}

_BINOCULAR_OP_2_INTERNAL_METHOD = {
    "+":    "add",
    "-":    "sub",
    "*":    "mul",
    "/":    "div",
    "%":    "mod",
    "<<":   "shl",
    ">>":   "shr",
    "&":    "and",
    "|":    "or",
    "^":    "xor",
}

def _gen_el_code(el, with_perm = False):
    mod = _curr_mod

    ecl = ["%d" % mod.id] if with_perm else []
    ecl += ["(%s)" % _gen_expr_code(e) for e in el]
    return ", ".join(ecl)

def _gen_expr_code(expr):
    mod = _curr_mod

    if expr.op in ("literal", "literal_int"):
        t = expr.arg
        if t.is_literal("nil"):
            return "nil"
        return "%s" % _gen_literal_name(t)

    if expr.op == "str_format":
        fmt, el = expr.arg
        fmt_code = _gen_str_literal(fmt)
        for e in el:
            assert e.op == "to_go_fmt_str"
        return "sw_obj_str_from_go_str(sw_util_sprintf(%s, %s))" % (fmt_code, _gen_el_code(el)) if el else fmt_code

    if expr.op == "type_assert_int":
        e = expr.arg
        return _gen_type_assert_int(_gen_expr_code(e))

    if expr.op == "int_to_obj":
        e = expr.arg
        return "sw_obj_int_from_go_int(%s)" % _gen_expr_code(e)

    if expr.op == "isinstanceof_this":
        result = expr.arg
        return "sw_util_%s" % ("true" if result else "false")

    if expr.op == "isinstanceof_int":
        e = expr.arg
        return "sw_util_isinstanceof_int(%s)" % _gen_expr_code(e)

    if expr.op == "isinstanceof":
        e, cls = expr.arg
        return "sw_obj_int_from_go_bool(func () bool {_, ok := (%s).(*%s); return ok}())" % (_gen_expr_code(e), _gen_mod_elem_name(cls))

    if expr.op == "func_obj":
        fo = expr.arg
        return _gen_fo_name(fo)

    if expr.op == "to_go_fmt_str":
        verb, e = expr.arg
        return "sw_util_to_go_fmt_str(%s, (%s))" % (_gen_str_literal("%" + verb), _gen_expr_code(e))

    if expr.op == "new_obj":
        cls, el = expr.arg
        assert cls.is_cls
        return "%s(%s)" % (_gen_new_obj_func_name(cls), _gen_el_code(el))

    if expr.op == "this":
        return "this"

    if expr.op == "this.attr":
        name = expr.arg
        return "this.m_%s" % name

    if expr.op == "call_this.method":
        name, el = expr.arg
        return "this.%s(%s)" % (_gen_methodimpl_name(name), _gen_el_code(el, with_perm = True))

    if expr.op == ".":
        e, name = expr.arg
        return "(%s).%s(%d)" % (_gen_expr_code(e), _gen_get_attr_method_name(name), mod.id)

    if expr.op == "call_method":
        e, name, el = expr.arg
        return "(%s).%s(%s)" % (_gen_expr_code(e), _gen_method_name(name), _gen_el_code(el, with_perm = True))

    if expr.op == "call_func":
        func, el = expr.arg
        assert func.is_func
        return "%s(%s)" % (_gen_mod_elem_name(func), _gen_el_code(el))

    if expr.op == "gv":
        gv = expr.arg
        return _gen_mod_elem_name(gv)

    if expr.op == "lv":
        name = expr.arg
        return "l_%s" % name

    if expr.op in ("tuple", "list"):
        cls = _get_builtins_cls(expr.op)
        el = expr.arg
        return "&%s{v: []sw_obj{%s}}" % (_gen_mod_elem_name(cls), _gen_el_code(el))

    if expr.op == "dict":
        kvel = expr.arg
        ecl = ["%s().reserve_space(sw_obj_int_from_go_int(%d))" % (_gen_new_obj_func_name(_get_builtins_cls("dict")), len(kvel))]
        for ek, ev in kvel:
            ecl.append(".%s(%d, (%s), (%s))" % (_gen_method_name("set"), mod.id, _gen_expr_code(ek), _gen_expr_code(ev)))
        return "".join(ecl)

    if expr.op == "!":
        e = expr.arg
        return "sw_obj_int_from_go_bool((%s) == 0)" % _gen_expr_code(e)

    if expr.op in ("~", "neg", "pos"):
        go_op = {"~": "^", "neg": "-", "pos": "+"}[expr.op]
        return "%s(%s)" % (go_op, _gen_expr_code(e))

    if expr.op in ("&&", "||"):
        ea, eb = expr.arg
        return "sw_obj_int_from_go_bool((%s) != 0 %s (%s) != 0)" % (_gen_expr_code(ea), expr.op, _gen_expr_code(eb))

    if expr.op in ("<", ">", "<=", ">=", "!=", "==", "!==", "==="):
        go_op = expr.op
        if go_op in ("!==", "==="):
            go_op = go_op[: -1]
        ea, eb = expr.arg
        return "sw_obj_int_from_go_bool((%s) %s (%s))" % (_gen_expr_code(ea), go_op, _gen_expr_code(eb))

    if expr.op in _BINOCULAR_OP_2_INTERNAL_METHOD:
        ea, eb = expr.arg
        return "(%s) %s (%s)" % (_gen_expr_code(ea), expr.op, _gen_expr_code(eb))

    if expr.op == "if-else":
        e_cond, ea, eb = expr.arg
        return ("func () %s {if (%s) != 0 {return (%s)} else {return (%s)}}()" %
                (_gen_tp(expr.tp), _gen_expr_code(e_cond), _gen_expr_code(ea), _gen_expr_code(eb)))

    swc_util.abort()

_BOOTER_START_PROG_FUNC_NAME = "Sw_booter_start_prog"

def _output_main_pkg():
    with _Code(_main_pkg_file, "main") as code:
        with code.new_blk("import"):
            code += '"%s"' % _prog_pkg_name
        with code.new_blk("func main()"):
            code += "%s.%s()" % (_prog_pkg_name, _BOOTER_START_PROG_FUNC_NAME)

def _output_booter():
    with _Code("%s/%s.booter.go" % (_out_prog_dir, _prog_pkg_name)) as code:
        init_std_lib_internal_mods_func_name = "init_std_lib_internal_mods"
        with code.new_blk("func %s()" % _BOOTER_START_PROG_FUNC_NAME):
            with code.new_blk("var %s = func ()" % init_std_lib_internal_mods_func_name):
                code += "%s()" % _gen_init_mod_func_name(swc_mod.builtins_mod)
            code += ("sw_booter_start_prog(%s, %s, %s)" %
                     (init_std_lib_internal_mods_func_name,
                      _gen_init_mod_func_name(swc_mod.main_mod),
                      _gen_mod_elem_name(swc_mod.main_mod.get_main_func())))

def _output_native_code(code, nc, fom):
    class FakeToken:
        def __init__(self, line_idx):
            self.src_fn     = nc.t.src_fn
            self.line_idx   = nc.t.line_idx + 1 + line_idx

    with code.new_native_code():
        for line_idx, line in enumerate(nc.line_list):
            s = ""
            for i in line:
                if isinstance(i, str):
                    s += i
                else:
                    assert isinstance(i, tuple)
                    mod_name, name = i
                    s += "%s_%d_%s" % (_gen_mod_name(swc_mod.mod_map[mod_name]), len(name), name)
            code.record_tb_info((FakeToken(line_idx), fom))
            code += s

def _output_simple_assign(code, lvalue, expr_or_expr_code):
    mod = _curr_mod

    expr = expr_code = None
    if isinstance(expr_or_expr_code, str):
        expr_code = expr_or_expr_code
    else:
        expr = expr_or_expr_code
        expr_code = _gen_expr_code(expr)

    def output_simple_assign_ex(code, lvalue, expr_code):
        if expr is not None:
            code.record_tb_info(expr.pos_info)

        if lvalue.op == "gv":
            gv = lvalue.arg
            code += "%s = (%s)" % (_gen_mod_elem_name(gv), expr_code)
            return

        if lvalue.op == "lv":
            name = lvalue.arg
            code += "l_%s = (%s)" % (name, expr_code)
            return

        if lvalue.op == "this.attr":
            name = lvalue.arg
            code += "this.m_%s = (%s)" % (name, expr_code)
            return

        if lvalue.op == ".":
            obj_expr, name = lvalue.arg
            code += "(%s).%s(%d, (%s))" % (_gen_expr_code(obj_expr), _gen_set_attr_method_name(name), mod.id, expr_code)
            return
        
        swc_util.abort()

    assert lvalue.is_lvalue
    output_simple_assign_ex(code, lvalue, expr_code)

_in_func = False
_ret_tp = None

def _output_stmt_list(code, stmt_list):
    mod = _curr_mod

    for stmt in stmt_list:
        if stmt.type == "native_code":
            _output_native_code(code, stmt.nc, stmt.fom)
            continue

        if stmt.type == "block":
            with code.new_blk(""):
                _output_stmt_list(code, stmt.stmt_list)
            continue

        if stmt.type == "def_func_obj":
            _output_func_obj_def(code, stmt.func_obj)
            continue

        if stmt.type == "var_def":
            code += "var l_%s %s %s" % (stmt.name, _gen_tp(stmt.tp),
                                        "" if stmt.init_expr is None else "= (%s)" % _gen_expr_code(stmt.init_expr))
            code += "_ = l_%s" % stmt.name
            continue

        if stmt.type == "assign":
            _output_simple_assign(code, stmt.lvalue, stmt.expr)
            continue

        if stmt.type == "expr":
            code.record_tb_info(stmt.expr.pos_info)
            code += _gen_expr_code(stmt.expr)
            continue

        if stmt.type == "defer":
            code.record_tb_info(stmt.expr.pos_info)
            code += "defer %s" % _gen_expr_code(stmt.expr)
            continue

        if stmt.type == "for":
            with code.new_blk(""):
                iter_var_name = _gen_tmp_var_name()
                code.record_tb_info(stmt.iter_expr.pos_info)
                code += "var %s sw_obj = (%s).%s(%d)" % (iter_var_name, _gen_expr_code(stmt.iter_expr), _gen_method_name("iter", 0), mod.id)
                assert len(stmt.for_var_map) == 1
                name, tp = stmt.for_var_map.iteritems().next()
                code += "var l_%s %s" % (name, _gen_tp(tp))
                code += "_ = l_%s" % name
                code.record_tb_info(stmt.iter_expr.pos_info)
                with code.new_blk("for %s.%s(%d) != 0" % (iter_var_name, _gen_method_name("is_valid"), mod.id), start_with_blank_line = False):
                    code.record_tb_info(stmt.iter_expr.pos_info)
                    next_code = "%s.%s(%d)" % (iter_var_name, _gen_method_name("next"), mod.id)
                    code += "l_%s = %s" % (name, _gen_type_assert_int(next_code) if tp.is_int else next_code)
                    _output_stmt_list(code, stmt.stmt_list)
            continue

        if stmt.type == "while":
            code.record_tb_info(stmt.expr.pos_info, adjust = 1)
            with code.new_blk("for (%s) != 0" % _gen_expr_code(stmt.expr)):
                _output_stmt_list(code, stmt.stmt_list)
            continue

        if stmt.type in ("break", "continue"):
            code += stmt.type
            continue

        if stmt.type == "if":
            assert len(stmt.if_expr_list) == len(stmt.if_stmt_list_list)
            for i, (if_expr, if_stmt_list) in enumerate(zip(stmt.if_expr_list, stmt.if_stmt_list_list)):
                code.record_tb_info(if_expr.pos_info, adjust = 1 if i == 0 else -1)
                with code.new_blk("%sif (%s) != 0" % ("" if i == 0 else "else ", _gen_expr_code(if_expr))):
                    _output_stmt_list(code, if_stmt_list)
            if stmt.else_stmt_list is not None:
                with code.new_blk("else"):
                    _output_stmt_list(code, stmt.else_stmt_list)
            continue

        if stmt.type == "return_default":
            if _ret_tp.is_int:
                expr_code = "0"
                if _in_func:
                    expr_code = "sw_obj_int_from_go_int(%s)" % expr_code
            else:
                expr_code = "nil"
            code += "return (%s)" % expr_code
            continue

        if stmt.type == "return":
            expr_code = _gen_expr_code(stmt.expr)
            if _ret_tp.is_int:
                assert stmt.expr.tp.is_int
                if _in_func:
                    expr_code = "sw_obj_int_from_go_int(%s)" % expr_code
            code.record_tb_info(stmt.expr.pos_info)
            code += "return (%s)" % expr_code
            continue

        swc_util.abort()

_METHOD_SIGN_CODE = "(perm int64, args ...sw_obj) sw_obj"

def _output_parse_arg_code(code, arg_map):
    arg_count = len(arg_map)
    with code.new_blk("if len(args) != %d" % arg_count):
        code += "sw_util_abort_on_method_arg_count_err(len(args), %d)" % arg_count
    for i, (name, tp) in enumerate(arg_map.iteritems()):
        arg_code = "args[%d]" % i
        code += "var l_%s = " % (name, _gen_type_assert_int(arg_code) if tp.is_int else arg_code)

def _output_func_obj_def(code, fo):
    global _in_func, _ret_tp

    arg_count = len(fo.arg_map)
    with code.new_blk("var %s sw_obj = &sw_fo_stru" % (_gen_fo_name(fo))):
        with code.new_blk("f: func %s" % (_METHOD_SIGN_CODE), start_with_blank_line = False, tail = ","):
            _output_parse_arg_code(code, fo.arg_map)
            _in_func = True
            _ret_tp = fo.tp
            _output_stmt_list(code, fo.stmt_list)
            _in_func = True
            _ret_tp = None
            code += "return %s" % ("sw_obj_int_from_go_int(0)" if fo.tp.is_int else "nil")

todo BEGIN

def _output_attr_method_default(code, cls_stru_name, cls_type_name, attr_name):
    exc_code = _gen_internal_simple_exc("NoAttr", "‘%s’没有属性‘%s’" % (cls_type_name, attr_name))
    throw_exc_code = _gen_throw_exc(exc_code)
    with code.new_blk("func (this *%s) %s(perm int64) sw_obj" % (cls_stru_name, _gen_get_attr_method_name(attr_name))):
        code += throw_exc_code
        code += 'panic("bug")'  #规避一下编译错误
    with code.new_blk("func (this *%s) %s(perm int64, v sw_obj)" % (cls_stru_name, _gen_set_attr_method_name(attr_name))):
        code += throw_exc_code

def _output_method_default(code, cls_stru_name, cls_type_name, method_name, arg_count):
    arg_name_list = [str(i) for i in xrange(arg_count)]
    with code.new_blk("func (this *%s) %s(%s) sw_obj" %
                      (cls_stru_name, _gen_method_name(method_name, arg_count), _gen_arg_def(arg_name_list, need_perm_arg = True))):
        if len(method_name) > 4 and method_name.startswith("__") and method_name.endswith("__"):
            simple_method_name = method_name[2 : -2]

            if (simple_method_name, arg_count) == ("init", 0):
                #默认的构造方法，空函数
                code += "return %s" % _gen_nil_literal()
                return

            if (simple_method_name, arg_count) == ("repr", 0):
                #默认的repr，简单输出类型和地址说明
                code += ("return sw_obj_str_from_go_str(sw_util_sprintf(%s, this.type_name(), this.addr()))" %
                         _gen_str_literal("<%s object at 0x%X>"))
                return

            if (simple_method_name, arg_count) == ("str", 0):
                #默认的str调用repr
                code += "return this.%s(perm)" % _gen_method_name("__repr__", 0)
                return

            if (simple_method_name, arg_count) == ("bool", 0):
                #默认的bool为true
                code += "return %s" % _gen_bool_literal(True)
                return

            if simple_method_name.startswith("i_") and arg_count == 1:
                #默认的增量运算是调用普通双目运算
                code += "return this.%s(perm, l_0)" % _gen_method_name("__%s__" % simple_method_name[2 :], 1)
                return

        if method_name.startswith("__") and method_name.endswith("__"):
            info = "没有实现内部方法"
        else:
            info = "没有方法"
        exc_code = _gen_internal_simple_exc("NoMethod", "‘%s’%s‘%s<%d>’" % (cls_type_name, info, method_name, arg_count))
        code += _gen_throw_exc(exc_code)
        code += 'panic("bug")'  #规避编译错误

_literal_token_id_set = set()

def _output_mod():
    mod = _curr_mod

    mod_file_name = "%s/%s.mod.%s.M.go" % (_out_prog_dir, _prog_pkg_name, _gen_mod_name(mod))
    with _Code(mod_file_name) as code:
        #全局域的native code
        for nc in mod.gnc_list:
            _output_native_code(code, nc, "")

        #字面量集合定义
        code += ""
        for t in mod.literal_list:
            assert t.id not in _literal_token_id_set
            _literal_token_id_set.add(t.id)
            prefix = "literal_"
            assert t.is_literal and t.type.startswith(prefix)
            literal_type = t.type[len(prefix) :]
            if literal_type in ("nil", "bool"):
                #这两个类型的字面量是全局唯一的，直接体现在目标代码中
                continue
            if literal_type == "int":
                v = str(t.value)
            elif literal_type == "float":
                v = t.value.hex()
            elif literal_type == "str":
                v = _gen_str_literal(t.value)
            else:
                swc_util.abort()
            code += "var %s sw_obj = &%s{v: (%s)}" % (_gen_literal_name(t), _gen_mod_elem_name(_get_builtins_cls(literal_type)), v)

        #全局变量定义
        code += ""
        for gv in mod.gv_map.itervalues():
            code += "var %s sw_obj = sw_obj_get_nil()" % _gen_mod_elem_name(gv)

        #模块初始化
        code += ""
        mod_inited_flag_name = "sw_env_inited_flag_of_mod_%s" % _gen_mod_name(mod)
        code += "var %s bool = false" % mod_inited_flag_name
        with code.new_blk("func %s()" % _gen_init_mod_func_name(mod), start_with_blank_line = False):
            with code.new_blk("if !%s" % mod_inited_flag_name):
                code += "%s = true" % mod_inited_flag_name
                for dep_mod_name in mod.dep_mod_set:
                    code += "%s()" % _gen_init_mod_func_name(swc_mod.mod_map[dep_mod_name])
                for gv_init in mod.gv_init_list:
                    _output_simple_assign(code, gv_init.var_def.to_lvalue(mod = mod), gv_init.expr)

        #函数定义
        for func in mod.func_map.itervalues():
            with code.new_blk("func %s(%s) sw_obj" % (_gen_mod_elem_name(func), _gen_arg_def(func.arg_map))):
                _output_stmt_list(code, func.stmt_list)
                code += "return %s" % _gen_nil_literal()

        #类的定义
        for cls in mod.cls_map.itervalues():
            sw_cls_name = _gen_mod_elem_name(cls)

            with code.new_blk("type %s struct" % sw_cls_name):
                for nc in cls.nc_list:
                    _output_native_code(code, nc, "")
                for attr in cls.attr_map.itervalues():
                    code += "m_%s sw_obj" % attr.name

            #内部使用的方法
            with code.new_blk("func (this *%s) type_name() string" % sw_cls_name):
                cls_name = _gen_cls_type_name(cls)
                code += "return %s" % _gen_str_literal(cls_name)
            with code.new_blk("func (this *%s) addr() uint64" % sw_cls_name):
                code += "return sw_util_obj_addr(this)"

            #属性的get和set方法
            for attr in cls.attr_map.itervalues():
                def output_attr_perm_checking(code):
                    if not attr.is_public:
                        with code.new_blk("if perm != %d" % mod.id):
                            code += _gen_throw_no_perm_exc("对属性‘%s’没有权限" % attr)
                with code.new_blk("func (this *%s) %s(perm int64) sw_obj" % (sw_cls_name, _gen_get_attr_method_name(attr.name))):
                    output_attr_perm_checking(code)
                    code += "return this.m_%s" % attr.name
                with code.new_blk("func (this *%s) %s(perm int64, v sw_obj)" % (sw_cls_name, _gen_set_attr_method_name(attr.name))):
                    output_attr_perm_checking(code)
                    code += "this.m_%s = v" % attr.name

            init_method_arg_count_set = set([0])    #所有构造方法的参数数量集合，用于生成对应的sw_new_obj_*函数

            #用户定义方法
            usr_def_method_sign_set = set()
            for method in cls.method_map.itervalues():
                arg_count = len(method.arg_map)
                assert (method.name, arg_count) not in usr_def_method_sign_set
                usr_def_method_sign_set.add((method.name, arg_count))
                sw_method_name = _gen_method_name(method.name, arg_count)
                with code.new_blk("func (this *%s) %s(%s) sw_obj" %
                                  (sw_cls_name, sw_method_name, _gen_arg_def(method.arg_map, need_perm_arg = True))):
                    if not method.is_public:
                        with code.new_blk("if perm != %d" % mod.id):
                            code += _gen_throw_no_perm_exc("对方法‘%s<%d>’没有调用权限" % (method, arg_count))
                    _output_stmt_list(code, method.stmt_list)
                    code += "return %s" % _gen_nil_literal()
                if method.name == "__init__":
                    #对于构造方法还要生成对应的sw_new_obj_*函数
                    init_method_arg_count_set.add(arg_count)

            #生成所有sw_new_obj_*函数
            for arg_count in init_method_arg_count_set:
                sw_new_obj_func_name = _gen_new_obj_func_name(cls, arg_count)
                arg_name_list = [str(i) for i in xrange(arg_count)]
                with code.new_blk("func %s(%s) *%s" % (sw_new_obj_func_name, _gen_arg_def(arg_name_list), sw_cls_name)):
                    code += "o := new(%s)" % sw_cls_name
                    code.record_tb_info(_POS_INFO_IGNORE)
                    code += "o.%s(%s)" % (_gen_method_name("__init__", arg_count),
                                          ", ".join([str(mod.id)] + ["l_%s" % name for name in arg_name_list]))
                    code += "return o"

            #补全其他属性的get和set
            for attr_name in [an for an in swc_mod.all_attr_name_set if an not in cls.attr_map]:
                _output_attr_method_default(code, sw_cls_name, _gen_cls_type_name(cls), attr_name)

            #补全其他方法
            for method_name, arg_count in [ms for ms in _all_method_sign_set if ms not in usr_def_method_sign_set]:
                _output_method_default(code, sw_cls_name, _gen_cls_type_name(cls), method_name, arg_count)

        #全局域的函数对象
        for fo in mod.gfo_list:
            _output_func_obj_def(code, fo)

def _output_util():
    with _Code("%s/%s.util.go" % (_out_prog_dir, _prog_pkg_name)) as code:
        #traceback信息
        with code.new_blk("var sw_util_tb_map = map[sw_util_go_tb]*sw_util_sw_tb"):
            for (go_file_name, go_line_no), tb_info in _tb_map.iteritems():
                if tb_info is None:
                    code += "sw_util_go_tb{file: %s, line: %d}: nil," % (_gen_str_literal(go_file_name), go_line_no)
                else:
                    sw_file_name, sw_line_no, sw_fom_name = tb_info
                    code += ("sw_util_go_tb{file: %s, line: %d}: &sw_util_sw_tb{file: %s, line: %d, fom_name: %s}," %
                             (_gen_str_literal(go_file_name), go_line_no, _gen_str_literal(sw_file_name), sw_line_no,
                              _gen_str_literal(sw_fom_name)))

        #sw_obj的定义
        with code.new_blk("type sw_obj interface"):
            code += "type_name() string"
            code += "addr() uint64"
            for name in swc_mod.all_attr_name_set:
                code += "%s(int64) sw_obj" % (_gen_get_attr_method_name(name))
                code += "%s(int64, sw_obj)" % (_gen_set_attr_method_name(name))
            for name, arg_count in _all_method_sign_set:
                code += "%s(%s) sw_obj" % (_gen_method_name(name, arg_count), ", ".join(["int64"] + ["sw_obj"] * arg_count))

        #所有函数对象类型的实现，就是针对所有出现的函数对象的参数数量，生成对应的匿名class实现
        for arg_count in swc_mod.func_obj_arg_count_set:
            fo_name = "func<%d>" % arg_count
            fo_stru_name = _gen_func_obj_stru_name(arg_count)
            with code.new_blk("type %s struct" % fo_stru_name):
                code += "f func (%s) sw_obj" % ", ".join(["sw_obj"] * arg_count)
            #对应的call方法
            arg_name_list = [str(i) for i in xrange(arg_count)]
            with code.new_blk("func (this *%s) %s(%s) sw_obj" %
                              (fo_stru_name, _gen_method_name("call", arg_count), _gen_arg_def(arg_name_list, need_perm_arg = True))):
                code += "return this.f(%s)" % ", ".join(["l_%s" % arg_name for arg_name in arg_name_list])
            #内部使用的方法
            with code.new_blk("func (this *%s) type_name() string" % fo_stru_name):
                code += "return %s" % _gen_str_literal(fo_name)
            with code.new_blk("func (this *%s) addr() uint64" % fo_stru_name):
                code += "return sw_util_obj_addr(this)"
            #补全属性的get和set
            for attr_name in swc_mod.all_attr_name_set:
                _output_attr_method_default(code, fo_stru_name, fo_name, attr_name)
            #补全其他方法
            for method_name, arg_count in [ms for ms in _all_method_sign_set if ms != ("call", arg_count)]:
                _output_method_default(code, fo_stru_name, fo_name, method_name, arg_count)

todo END

def _make_prog():
    if platform.system() in ("Darwin", "Linux"):
        try:
            p = subprocess.Popen(["go", "env", "GOPATH"], stdout = subprocess.PIPE)
        except OSError:
            swc_util.exit("无法执行go命令")
        rc = p.wait()
        if rc != 0:
            swc_util.exit("通过go env获取GOPATH失败")
        go_path = p.stdout.read().strip()
        os.environ["GOPATH"] = out_dir + ":" + go_path
        rc = os.system("go build -o %s %s" % (_exe_file, _main_pkg_file))
        if rc != 0:
            swc_util.exit("go build失败")
    else:
        swc_util.exit("不支持在平台'%s'生成可执行程序" % platform.system())

def output():
    output_start_time = time.time()
    swc_util.vlog("开始输出go代码")

    _init_all_method_name_set()

    global _out_prog_dir, _prog_pkg_name, _exe_file, _main_pkg_file

    main_mod_name = swc_mod.main_mod.name

    _prog_pkg_name = "sw_prog_" + main_mod_name

    _out_prog_dir = "%s/src/%s" % (out_dir, _prog_pkg_name)

    shutil.rmtree(out_dir, True)
    os.makedirs(_out_prog_dir)

    _exe_file = "%s/%s" % (out_dir, main_mod_name)

    _main_pkg_file = "%s/src/%s.P.go" % (out_dir, _prog_pkg_name)

    _output_main_pkg()
    _output_booter()

    global _curr_mod
    for _curr_mod in swc_mod.mod_map.itervalues():
        _output_mod()

    _output_util()

    swc_util.vlog("go代码输出完毕，耗时%.2f秒" % (time.time() - output_start_time))

    go_build_start_time = time.time()
    swc_util.vlog("开始执行go build")
    _make_prog()
    swc_util.vlog("go build完毕，耗时%.2f秒" % (time.time() - go_build_start_time))
