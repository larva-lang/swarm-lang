#coding=utf8

import shutil, os, subprocess, platform, time

import swc_util, swc_mod

out_dir = None

_out_prog_dir = _prog_pkg_name = _exe_file = _main_pkg_file = _all_method_sign_set = None

_POS_INFO_IGNORE = object()

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
            tb_info = t.src_file, t.line_no, str(fom)
        _tb_map[(self.file_path_name, len(self.line_list) + 1 + adjust)] = tb_info

def _init_all_method_sign_set():
    #将所有可能的sw_method_*签名整合出来，不包括内部使用的类似type_name之类的

    global _all_method_sign_set
    _all_method_sign_set = swc_util.OrderedSet()

    #内部方法

    def add_internal_method_sign(simple_name, arg_count):
        _all_method_sign_set.add(("__%s__" % simple_name, arg_count))
    #默认构造方法
    add_internal_method_sign("init", 0)
    #字符串表示相关
    add_internal_method_sign("repr", 0)
    add_internal_method_sign("str", 0)
    #比较方法
    add_internal_method_sign("cmp", 1)
    #布尔值
    add_internal_method_sign("bool", 0)
    #包含元素相关
    add_internal_method_sign("haselem", 1)
    add_internal_method_sign("getelem", 1)
    add_internal_method_sign("setelem", 2)
    add_internal_method_sign("getslice", 2)
    add_internal_method_sign("setslice", 3)
    #双目数值运算
    for name in "add", "sub", "mul", "div", "mod", "shl", "shr", "and", "or", "xor":
        for prefix in "", "i", "r":
            add_internal_method_sign(prefix + name, 1)
    #单目数值运算
    for name in "inv", "pos", "neg":
        add_internal_method_sign(name, 0)

    #用户定义方法
    for name, arg_count in swc_mod.all_method_sign_set:
        _all_method_sign_set.add((name, arg_count))

    #函数对象的call方法
    for func_obj in swc_mod.func_objs:
        _all_method_sign_set.add(("call", len(func_obj.arg_map)))

_BOOTER_START_PROG_FUNC_NAME = "Sw_booter_start_prog"

def _output_main_pkg():
    with _Code(_main_pkg_file, "main") as code:
        with code.new_blk("import"):
            code += '"%s"' % _prog_pkg_name
        with code.new_blk("func main()"):
            code += "%s.%s()" % (_prog_pkg_name, _BOOTER_START_PROC_FUNC_NAME)

def _output_booter():
    with _Code("%s/%s.booter.go" % (_out_prog_dir, _prog_pkg_name)) as code:
        init_std_lib_internal_mods_func_name = "init_std_lib_internal_mods"
        with code.new_blk("func %s()" % _BOOTER_START_PROG_FUNC_NAME):
            with code.new_blk("var %s = func ()" % init_std_lib_internal_mods_func_name):
                code += "%s()" % _gen_init_mod_func_name(swc_mod.builtins_mod)
            code += ("sw_booter_start_prog(%s, %s, %s)" %
                     (init_std_lib_internal_mods_func_name,
                      _gen_init_mod_func_name(swc_mod.main_mod),
                      _gen_func_name(swc_mod.main_mod.get_main_func())))

def _output_mod(mod):
    todo

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
