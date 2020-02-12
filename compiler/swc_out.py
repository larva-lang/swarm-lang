#coding=utf8

import shutil, os, subprocess, platform, time

import swc_util, swc_mod

out_dir = None

_out_prog_dir = _prog_pkg_name = _exe_file = _main_pkg_file = _all_method_sign_set = None

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

def _init_all_method_sign_set():
    #将所有可能的sw_method_*签名整合出来，不包括内部使用的类似type_name之类的

    global _all_method_sign_set
    _all_method_sign_set = swc_util.OrderedSet()

    #内部方法
    for name, arg_count in swc_mod.internal_method_sign_set:
        _all_method_sign_set.add((name, arg_count))

    #用户定义方法
    for name, arg_count in swc_mod.all_usr_method_sign_set:
        _all_method_sign_set.add((name, arg_count))

    #函数对象的call方法
    for fo_arg_count in swc_mod.func_obj_arg_count_set:
        _all_method_sign_set.add(("call", len(func_obj.arg_map)))

#gens-------------------------------------------------------------

def _gen_mod_name(mod):
    return "%d_%s" % (len(mod.name), mod.name)

def _gen_init_mod_func_name(mod):
    return "sw_env_init_mod_" + _gen_mod_name(mod)

def _gen_mod_elem_name(elem):
    for i in "cls", "func", "gv":
        if eval("elem.is_%s" % i):
            suffix = "_%d" % len(elem.arg_map) if i == "func" else ""
            return "sw_%s_%s_%d_%s%s" % (i, _gen_mod_name(elem.mod), len(elem.name), elem.name, suffix)

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

def _gen_method_name(name, arg_count):
    return "sw_method_%s_%d" % (name, arg_count)

def _gen_get_attr_method_name(name):
    return "sw_attr_%s" % name

def _gen_set_attr_method_name(name):
    return "sw_setattr_%s" % name

def _gen_literal_name(t):
    return "sw_literal_%d" % t.id

def _gen_arg_def(arg_map, need_perm_arg = False):
    al = ["l_%s sw_obj" % name for name in arg_map]
    if need_perm_arg:
        al = ["perm int64"] + al
    return ", ".join(al)

def _gen_nil_literal():
    return _gen_mod_elem_name(swc_mod.builtins_mod.gv_map["_nil_obj"])

def _gen_bool_literal(b):
    return _gen_mod_elem_name(swc_mod.builtins_mod.gv_map["_bool_obj_%s" % ("true" if b else "false")])

def _gen_new_obj_func_name(cls, arg_count):
    return "sw_new_obj_%s_%d" % (_gen_mod_elem_name(cls), arg_count)

def _gen_func_obj_stru_name(arg_count):
    return "sw_fo_stru_%d" % arg_count

def _gen_throw_no_perm_exc(info):
    return _gen_throw_exc("sw_exc_make_no_perm_exc(`%s`)" % info)

def _gen_throw_exc(exc):
    return "%s(%s)" % (_gen_mod_elem_name(swc_mod.builtins_mod.func_map[("throw", 1)]), exc)

#gens end-------------------------------------------------------------

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
            self.line_idx   = nc.t.line_idx + 1 + line_idx + 1

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

def _output_var_def_assign(code, var_def, expr, is_gv = False):
    "todo"
    '''
    for gv in module.global_var_map.itervalues():
        if gv.expr is not None:
            code.record_tb_info(gv.expr.pos_info)
            code += "%s = %s" % (_gen_gv_name(gv), _gen_expr_code(gv.expr))
    '''

def _output_stmt_list(code, stmt_list):
    "todo"

def _output_func_obj_def(code, fo):
    arg_count = len(fo.arg_map)
    with code.new_blk("var sw_fo_%d sw_obj = &%s" % (fo.id, _gen_func_obj_stru_name(arg_count))):
        with code.new_blk("f: func (%s) sw_obj" % (_gen_arg_def(fo.arg_map)), start_with_blank_line = False, tail = ","):
            _output_stmt_list(code, fo.stmt_list)

def _output_attr_method_default(code, cls_stru_name, cls_name, attr_name):
    exc_code = "sw_exc_make_no_attr_exc(`‘%s’没有属性‘%s’`)" % (cls_name, attr_name)
    throw_exc_code = _gen_throw_exc(exc_code)
    with code.new_blk("func (this *%s) %s(perm int64) sw_obj" % (cls_stru_name, _gen_get_attr_method_name(attr_name))):
        code += throw_exc_code
        code += 'panic("bug")'  #规避一下编译错误
    with code.new_blk("func (this *%s) %s(perm int64, v sw_obj)" % (cls_stru_name, _gen_set_attr_method_name(attr_name))):
        code += throw_exc_code

def _output_method_default(code, cls_stru_name, cls_name, method_name, arg_count):
    arg_name_list = [str(i) for i in xrange(arg_count)]
    with code.new_blk("func (this *%s) %s(%s) sw_obj" %
                      (cls_stru_name, _gen_method_name(method_name, arg_count), _gen_arg_def(arg_name_list, need_perm_arg = True))):
        def output_method_not_impl(code):
            if method_name.startswith("__") and method_name.endswith("__"):
                info = "没有实现内部方法"
            else:
                info = "没有方法"
            exc_code = "sw_exc_make_no_method_exc(`‘%s’%s‘%s<%d>’`)" % (cls_name, info, method_name, arg_count)
            code += _gen_throw_exc(exc_code)
            code += 'panic("bug")'  #规避编译错误

        if len(method_name) > 4 and method_name.startswith("__") and method_name.endswith("__"):
            simple_method_name = method_name[2 : -2]

            if (simple_method_name, arg_count) == ("init", 0):
                #默认的构造方法，空函数
                code += "return %s" % _gen_nil_literal()

            elif (simple_method_name, arg_count) == ("repr", 0):
                #默认的repr，简单输出类型和地址说明
                code += "return sw_str_from_go_str(sw_util_sprintf(`<%s object at 0x%X>`, this.type_name(), this.addr()))"

            elif (simple_method_name, arg_count) == ("str", 0):
                #默认的str调用repr
                code += "return this.%s(perm)" % _gen_method_name("__repr__", 0)

            elif (simple_method_name, arg_count) == ("bool", 0):
                #默认的bool为true
                code += "return %s" % _gen_bool_literal(True)

            elif simple_method_name in ("cmp", "eq", "add", "sub", "mul", "div", "mod", "shl", "shr", "and", "or", "xor") and arg_count == 1:
                #默认的双目运算是调用反向操作
                code += "return l_0.%s(perm, this)" % _gen_method_name("__r_%s__" % simple_method_name, 1)

            elif simple_method_name.startswith("i_") and arg_count == 1:
                #默认的增量运算是调用普通双目运算
                code += "return this.%s(perm, l_0)" % _gen_method_name("__%s__" % simple_method_name[2 :], 1)

            else:
                output_method_not_impl(code)

        else:
            output_method_not_impl(code)

_literal_token_id_set = set()

def _output_mod(mod):
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
            if literal_type in ("int", "uint"):
                v = str(t.value)
            elif literal_type == "float":
                v = t.value.hex()
            elif literal_type == "str":
                v = _gen_str_literal(t.value)
            else:
                swc_util.abort()
            code += ("var %s sw_obj = &%s{v: (%s)}" %
                     (_gen_literal_name(t), _gen_mod_elem_name(swc_mod.builtins_mod.cls_map[literal_type]), v))

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
                    _output_var_def_assign(gv_init.var_def, gv_init.expr, is_gv = True)

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
                code += "return %s" % _gen_str_literal(str(cls))
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
                    sw_new_obj_func_name = _gen_new_obj_func_name(cls, arg_count)
                    with code.new_blk("func %s(%s) *%s" % (sw_new_obj_func_name, _gen_arg_def(method.arg_map), sw_cls_name)):
                        code += "o := new(%s)" % sw_cls_name
                        code.record_tb_info(_POS_INFO_IGNORE)
                        code += "o.%s(%s)" % (sw_method_name, ", ".join([str(mod.id)] + ["l_%s" % name for name in method.arg_map]))
                        code += "return o"

            #补全其他属性的get和set
            for attr_name in [an for an in swc_mod.all_attr_name_set if an not in cls.attr_map]:
                _output_attr_method_default(code, sw_cls_name, str(cls), attr_name)

            #补全其他方法
            for method_name, arg_count in [ms for ms in _all_method_sign_set if ms not in usr_def_method_sign_set]:
                _output_method_default(code, sw_cls_name, str(cls), method_name, arg_count)

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
                              (fo_stru_name, _gen_method_name(("call", arg_count)), _gen_arg_def(arg_name_list, need_perm_arg = True))):
                code += "return this.f(%s)" % ", ".join(["l_%s" % arg_name for arg_name in arg_name_list])
            #内部使用的方法
            with code.new_blk("func (this *%s) type_name() string" % fo_stru_name):
                code += "return %s" % _gen_str_literal(fo_name)
            with code.new_blk("func (this *%s) addr() uint64" % sw_cls_name):
                code += "return sw_util_obj_addr(this)"
            #补全属性的get和set
            for attr_name in swc_mod.all_attr_name_set:
                _output_attr_method_default(code, fo_stru_name, fo_name, attr_name)
            #补全其他方法
            for method_name, arg_count in [ms for ms in _all_method_sign_set if ms != ("call", arg_count)]:
                _output_method_default(code, fo_stru_name, fo_name, method_name, arg_count)

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

    _init_all_method_sign_set()

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
    for mod in swc_mod.mod_map.itervalues():
        _output_mod(mod)
    _output_util()

    swc_util.vlog("go代码输出完毕，耗时%.2f秒" % (time.time() - output_start_time))

    go_build_start_time = time.time()
    swc_util.vlog("开始执行go build")
    _make_prog()
    swc_util.vlog("go build完毕，耗时%.2f秒" % (time.time() - go_build_start_time))
