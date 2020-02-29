#coding=utf8

import os

import swc_util, swc_token, swc_expr, swc_stmt, swc_type

mod_path = None

builtins_mod = None
main_mod = None
mod_map = swc_util.OrderedDict()

def _make_internal_method_sign_set():
    s = swc_util.OrderedSet()

    def add_internal_method_sign(simple_name, arg_count):
        s.add(("__%s__" % simple_name, arg_count))

    #字符串表示相关
    add_internal_method_sign("repr", 0)
    add_internal_method_sign("str", 0)

    return s

all_attr_name_set           = swc_util.OrderedSet()             #用于存储所有定义的属性名字
all_usr_method_sign_set     = swc_util.OrderedSet()             #用于存储所有定义的方法的签名，元素为(方法名, 参数数量)
internal_method_sign_set    = _make_internal_method_sign_set()  #用于存储所有内部方法的签名

def parse_var_name_def(token_list):
    t, name = token_list.pop_name()
    tp = swc_type.parse_type(t, token_list)
    return t, name, tp

def _parse_decr_set(token_list):
    decr_set = set()
    while True:
        t = token_list.peek()
        for decr in "public", "final":
            if t.is_reserved(decr):
                if decr in decr_set:
                    t.syntax_err("重复的修饰'%s'" % decr)
                decr_set.add(decr)
                token_list.pop()
                break
        else:
            return decr_set

def _parse_arg_map(token_list):
    arg_map = swc_util.OrderedDict()
    if token_list.peek().is_sym(")"):
        token_list.pop()
    else:
        def parse_single_arg():
            t, name, tp = parse_var_name_def(token_list)
            if name in arg_map:
                t.syntax_err("参数重复定义")
            arg_map[name] = tp
        swc_util.parse_items(token_list, parse_single_arg, ")")
    return arg_map

def precompile(main_mod_name):
    global builtins_mod, main_mod
    mod_map["__builtins"] = builtins_mod = Mod("__builtins")
    mod_map[main_mod_name] = main_mod = Mod(main_mod_name)

    compiling_set = set() #需要预处理的模块全名集合
    for m in mod_map.itervalues():
        compiling_set |= m.dep_mod_set
    while compiling_set:
        new_compiling_set = set()
        for mod_name in compiling_set:
            if mod_name in mod_map:
                #已预处理过
                continue
            mod_map[mod_name] = m = Mod(mod_name)
            new_compiling_set |= m.dep_mod_set
        compiling_set = new_compiling_set
    assert mod_map.value_at(0) is builtins_mod

    main_mod._check_main_func()

def compile():
    for m in mod_map.itervalues():
        m._compile()

class NativeCode:
    def __init__(self, mod, t):
        self.mod = mod
        self.t = t
        self.line_list = t.value[:]
        self._parse()

    def _parse(self):
        #逐行扫描，分析标识符的宏替换
        for line_idx, line in enumerate(self.line_list):
            self.line_list[line_idx] = self._analyze_name_macro(line_idx, line)

    def _analyze_name_macro(self, line_idx, line):
        #native code的token类，只用于报告错误
        class NativeCodeToken:
            def __init__(token_self, pos):
                token_self.pos_desc = "文件[%s]行[%d]列[%d]" % (self.t.src_fn, self.t.line_idx + 1 + line_idx + 1, pos + 1)
            def syntax_err(self, msg):
                swc_util.exit("%s %s" % (self.pos_desc, msg))

        #line转换为一个列表，列表元素为字符串或元组，字符串为单行的子串，元组为解析后的标识符宏(mod_name, name)
        result = []
        idx = 0
        while True:
            pos = line.find("@<<", idx)
            if pos < 0:
                result.append(line[idx :])
                return result
            result.append(line[idx : pos])
            token = NativeCodeToken(pos)
            end_pos = line.find(">>", pos + 3)
            if end_pos < 0:
                token.syntax_err("非法的标识符宏：找不到结束标记'>>'")
            macro = line[pos + 3 : end_pos]
            idx = end_pos + 2
            #开始分析macro
            if "." in macro:
                #带模块的macro
                try:
                    mod_name, name = macro.split(".")
                except ValueError:
                    token.syntax_err("非法的标识符宏")
                if not swc_token.is_valid_name(mod_name):
                    token.syntax_err("非法的标识符宏")

                if mod_name not in self.mod.dep_mod_set:
                    #native_code引用了一个没有被预处理导入的模块，报错
                    token.syntax_err("模块'%s'需要显式导入" % mod_name)
            elif macro.startswith(":"):
                #__builtin模块name简写形式
                mod_name = "__builtins"
                name = macro[1 :]
            else:
                #单个name
                mod_name = self.mod.name
                name = macro
            if not swc_token.is_valid_name(name):
                token.syntax_err("非法的标识符宏")
            result.append((mod_name, name))

class _ModElem:
    def __init__(self):
        self.is_cls     = isinstance(self, _Cls)
        self.is_func    = isinstance(self, _Func)
        self.is_gv      = isinstance(self, _Gv)
        assert [self.is_cls, self.is_func, self.is_gv].count(True) == 1

class _Attr:
    def __init__(self, cls, decr_set, name_token, name, tp):
        self.cls        = cls
        self.decr_set   = decr_set
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name
        self.tp         = tp

        all_attr_name_set.add(self.name)

    __repr__ = __str__ = lambda self : "%s.%s" % (self.cls, self.name)

class _Method:
    def __init__(self, cls, decr_set, name_token, name, arg_map, tp, block_token_list):
        self.cls        = cls
        self.decr_set   = decr_set
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name
        self.arg_map    = arg_map
        self.tp         = tp

        self.block_token_list   = block_token_list
        self.stmt_list          = None

        all_usr_method_sign_set.add((self.name, len(self.arg_map)))

    __repr__ = __str__ = lambda self : "%s.%s" % (self.cls, self.name)

    def _compile(self):
        self.stmt_list = swc_stmt.Parser(self.block_token_list, self.cls.mod, self.cls, self).parse((self.arg_map.copy(),), 0)
        self.block_token_list.pop_sym("}")
        assert not self.block_token_list
        del self.block_token_list

class _Cls(_ModElem):
    def __init__(self, mod, decr_set, name_token, name, ext_cls_name_list):
        _ModElem.__init__(self)

        self.mod                = mod
        self.is_public          = "public" in decr_set
        self.name_token         = name_token
        self.name               = name
        self.ext_cls_name_list  = ext_cls_name_list

        self.ext_cls_expand_stat = "to_expand"

        self.nc_list            = []
        self.attr_map           = swc_util.OrderedDict()
        self.method_map         = swc_util.OrderedDict()
        self.method_name_set    = swc_util.OrderedSet()

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

    def _parse(self, token_list):
        while True:
            t = token_list.peek()
            if t.is_sym("}"):
                break

            if t.is_native_code:
                token_list.pop()
                self.nc_list.append(NativeCode(self.mod, t))
                continue

            #解析修饰
            decr_set = _parse_decr_set(token_list)
            if decr_set - set(["public"]):
                t.syntax_err("方法或属性只能用public修饰")

            t = token_list.pop()

            if t.is_reserved("var"):
                #属性定义
                def parse_single_attr():
                    t, name, tp = parse_var_name_def(token_list)
                    if name.startswith("__") and name.endswith("__"):
                        t.syntax_err("属性不能使用内建方法名的样式")
                    self._check_redefine(t, name)
                    self.attr_map[name] = _Attr(self, decr_set, t, name, tp)
                swc_util.parse_items(token_list, parse_single_attr, ";")
                continue

            if t.is_reserved("func"):
                #方法定义
                t, name = token_list.pop_name()
                token_list.pop_sym("(")
                arg_map = _parse_arg_map(token_list)
                self._check_redefine(t, name)
                tp = swc_type.parse_type(t, token_list)
                token_list.pop_sym("{")
                block_token_list, sym = swc_token.parse_token_list_until_sym(token_list, ("}",))
                assert sym == "}"
                self.method_map[name] = _Method(self, decr_set, t, name, arg_map, tp, block_token_list)
                self.method_name_set.add(name)
                continue

            t.syntax_err("需要属性或方法定义")

    def _check_redefine(self, t, name):
        for m in self.attr_map, self.method_map:
            if name in m:
                t.syntax_err("方法或属性名‘%s’重定义" % name)

    def _expand_ext_cls(self, chain = ""):
        if self.ext_cls_expand_stat == "expanded":
            assert self.ext_cls_name_list is None
            return

        chain += ("->" if chain else "") + str(self)

        if self.ext_cls_expand_stat == "expanding":
            self.name_token.syntax_err("类的扩展存在环形依赖：[%s]" % chain)

        assert self.ext_cls_expand_stat == "to_expand"
        self.ext_cls_expand_stat = "expanding"

        ext_attr_map = swc_util.OrderedDict()
        ext_method_map = swc_util.OrderedDict()
        for t, cls_name in self.ext_cls_name_list:
            cls = self.mod.cls_map.get(cls_name)
            if cls is None:
                t.syntax_err("找不到类‘%s’，必须为本模块的类" % cls_name)
            cls._expand_ext_cls(chain)
            #直接扩展NativeCode块，正确性由开发者保证
            self.nc_list += cls.nc_list
            #统计扩展属性，需要严格唯一
            for attr in cls.attr_map.itervalues():
                self_attr = self.attr_map.get(attr.name)
                if self_attr is not None:
                    self_attr.name_token.syntax_err("属性‘%s’已从‘%s’扩展得到，不能重复定义" % (attr.name, cls))
                ext_attr = ext_attr_map.get(attr.name)
                if ext_attr is not None:
                    self.name_token.syntax_err("属性‘%s’有多个扩展来源：‘%s’、‘%s’等" % (attr.name, ext_attr.cls, cls))
                ext_attr_map[attr.name] = attr
            #统计扩展方法，允许当前类重写
            for method_name, method in cls.method_map.iteritems():
                if method_name in self.method_map:
                    #忽略已重写的
                    continue
                ext_method = ext_method_map.get(method_name)
                if ext_method is not None:
                    self.name_token.syntax_err("方法‘%s’有多个扩展来源：‘%s’、‘%s’等" % (method_name, ext_method.cls, cls))
                ext_method_map[method_name] = method

        for ext_attr in ext_attr_map.itervalues():
            assert ext_attr.name not in self.attr_map
            self.attr_map[ext_attr.name] = _Attr(self, ext_attr.decr_set, ext_attr.name_token, ext_attr.name, ext_attr.tp)
        for ext_method in ext_method_map.itervalues():
            assert ext_method.name not in self.method_map
            self.method_map[ext_method.name] = _Method(self, ext_method.decr_set, ext_method.name_token, ext_method.name,
                                                       ext_method.arg_map.copy(), ext_method.tp, ext_method.block_token_list.copy())

        self.ext_cls_name_list = None
        self.ext_cls_expand_stat = "expanded"

    def _compile(self):
        for method in self.method_map.itervalues():
            method._compile()

    def get_construct_method(self):
        return self.method_map.get("__init__")

class _Func(_ModElem):
    def __init__(self, mod, decr_set, name_token, name, arg_map, tp, block_token_list):
        _ModElem.__init__(self)

        self.mod        = mod
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name
        self.arg_map    = arg_map
        self.tp         = tp

        self.block_token_list   = block_token_list
        self.stmt_list          = None

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

    def _compile(self):
        self.stmt_list = swc_stmt.Parser(self.block_token_list, self.mod, None, self).parse((self.arg_map.copy(),), 0)
        self.block_token_list.pop_sym("}")
        assert not self.block_token_list
        del self.block_token_list

class _Gv(_ModElem):
    def __init__(self, mod, decr_set, name_token, name, tp, expr_token_list):
        _ModElem.__init__(self)

        self.mod        = mod
        self.is_public  = "public" in decr_set
        self.is_final   = "final" in decr_set
        self.name_token = name_token
        self.name       = name
        self.tp         = tp

        self.expr_token_list    = expr_token_list
        self.expr               = None

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

    def _compile(self):
        if self.expr_token_list is not None:
            self.expr = swc_expr.Parser(self.expr_token_list, self.mod, None, None, self.mod).parse((), None)
            _, sym = self.expr_token_list.pop_sym()
            assert sym in (";", ",")
            assert not self.expr_token_list
            if self.tp != self.expr.tp:
                self.name_token.syntax_err("初始化表达式与全局变量类型不匹配")
        del self.expr_token_list

class Mod:
    def __init__(self, mn):
        self.id = swc_util.new_id()

        self.name = mn
        self.src_fns = self._find_mod_files()

        self.literal_list   = None
        self.dep_mod_set    = set()
        self.gnc_list       = []
        self.cls_map        = swc_util.OrderedDict()
        self.func_map       = swc_util.OrderedDict()
        self.gv_map         = swc_util.OrderedDict()
        self.gv_init_list   = []
        self.gfo_list       = []

        self._precompile()
        self._check_name_conflict()
        self._expand_ext_cls()

    __repr__ = __str__ = lambda self : self.name

    def _find_mod_files(self):
        for d in mod_path:
            mod_fn = "%s/%s.sw" % (d, self.name)
            if os.path.isfile(mod_fn):
                fns = [mod_fn]
                incl_dn = "%s/%s.include" % (d, self.name)
                if os.path.isdir(incl_dn):
                    incl_fns = sorted(["%s/%s" % (incl_dn, fn) for fn in os.listdir(incl_dn) if fn.endswith(".sw")])
                    fns += incl_fns
                return fns

        swc_util.exit("找不到模块‘%s’" % self.name)

    def _precompile(self):
        assert self.src_fns
        token_list = swc_token.Parser(self.src_fns[0]).parse()
        for fn in self.src_fns[1 :]:
            tl = swc_token.Parser(fn).parse()
            token_list.extend_file(tl)
        self._parse_text(token_list)

    def _parse_text(self, token_list):
        self.literal_list = [t for t in token_list if t.is_literal]

        import_end = False
        while token_list:
            if token_list.try_pop_file_end():
                continue

            t = token_list.peek()

            #解析import
            if t.is_reserved("import"):
                #import
                if import_end:
                    t.syntax_err("import必须在模块代码最前面")
                self._parse_import(token_list)
                continue
            import_end = True

            #解析global域的native_code
            if t.is_native_code:
                token_list.pop()
                self.gnc_list.append(NativeCode(self, t))
                continue

            #解析修饰
            decr_set = _parse_decr_set(token_list)

            #解析各种定义
            t = token_list.pop()

            if t.is_reserved("class"):
                #类
                if decr_set - set(["public"]):
                    t.syntax_err("类只能用public修饰")
                self._parse_cls(decr_set, token_list)
                continue

            if t.is_reserved("func"):
                #函数
                if decr_set - set(["public"]):
                    t.syntax_err("函数只能用public修饰")
                self._parse_func(decr_set, token_list)
                continue

            if t.is_reserved("var"):
                #全局变量定义
                if decr_set - set(["public", "final"]):
                    t.syntax_err("全局变量只能用public、final修饰")
                self._parse_gv(decr_set, token_list)
                continue

            t.syntax_err()

    def _parse_import(self, token_list):
        t = token_list.pop()
        assert t.is_reserved("import")
        def parse_single_import():
            t, name = token_list.pop_name()
            if name in self.dep_mod_set:
                t.syntax_err("模块重复导入")
            if not self.name.startswith("__") and name.startswith("__"):
                t.syntax_err("普通模块不能显式导入内部模块‘%s’" % name)
            self.dep_mod_set.add(name)
        swc_util.parse_items(token_list, parse_single_import, ";")

    def _parse_cls(self, decr_set, token_list):
        t, name = token_list.pop_name()
        self._check_redefine(t, name)
        ext_cls_name_list = []
        if token_list.peek().is_sym("("):
            #扩展了其他类
            token_list.pop_sym("(")
            def parse_single_name():
                t, ext_cls_name = token_list.pop_name()
                ext_cls_name_list.append((t, ext_cls_name))
            swc_util.parse_items(token_list, parse_single_name, ")")
        token_list.pop_sym("{")
        cls = _Cls(self, decr_set, t, name, ext_cls_name_list)
        cls._parse(token_list)
        token_list.pop_sym("}")
        self.cls_map[name] = cls

    def _parse_func(self, decr_set, token_list):
        t, name = token_list.pop_name()
        self._check_redefine(t, name)
        token_list.pop_sym("(")
        arg_map = _parse_arg_map(token_list)
        tp = swc_type.parse_type(t, token_list)
        token_list.pop_sym("{")
        block_token_list, sym = swc_token.parse_token_list_until_sym(token_list, ("}",))
        assert sym == "}"
        self.func_map[name] = _Func(self, decr_set, t, name, arg_map, tp, block_token_list)

    def _parse_gv(self, decr_set, token_list):
        def parse_single_gv():
            t, name, tp = parse_var_name_def(token_list)
            self._check_redefine(t, name)
            if token_list.peek().is_sym("="):
                token_list.pop_sym("=")
                block_token_list, _ = swc_token.parse_token_list_until_sym(token_list, (",", ";"))
                token_list.revert()
            else:
                block_token_list = None
            self.gv_map[name] = _Gv(self, decr_set, t, name, tp, block_token_list)
        swc_util.parse_items(token_list, parse_single_gv, ";")

    def _check_redefine(self, t, name):
        if name in self.dep_mod_set:
            t.syntax_err("定义的名字和导入模块名重名")
        #类或全局变量
        for i in self.cls_map, self.func_map, self.gv_map:
            if name in i:
                t.syntax_err("与同模块中已定义的其他名字冲突")

    def iter_mod_elems(self):
        for m in self.cls_map, self.func_map, self.gv_map:
            for elem in m.itervalues():
                yield elem

    def get_elem(self, name):
        for elem in self.iter_mod_elems():
            if elem.name == name:
                return elem
        else:
            return None

    def public_name_set(self):
        name_set = set()
        for elem in self.iter_mod_elems():
            if elem.is_public:
                name_set.add(elem.name)
        return name_set

    def name_set(self):
        name_set = set()
        for elem in self.iter_mod_elems():
            name_set.add(elem.name)
        return name_set

    def _check_name_conflict(self):
        builtins_name_set = set() if builtins_mod is None else builtins_mod.public_name_set()

        #检查当前模块和内建模块的public名字是否有冲突，给出警告
        for elem in self.iter_mod_elems():
            if elem.name in builtins_name_set:
                elem.name_token.warn("‘%s’在所在模块中隐藏了同名内建元素" % elem)

        #检查所有方法和函数的参数名的冲突问题
        def arg_maps():
            for cls in self.cls_map.itervalues():
                for method in cls.method_map.itervalues():
                    yield method.arg_map
            for func in self.func_map.itervalues():
                yield func.arg_map
        mod_name_set = self.name_set()
        for arg_map in arg_maps():
            for name, tp in arg_map.iteritems():
                check_lv_name_conflict(name, tp.token, self)

    def _expand_ext_cls(self):
        for cls in self.cls_map.itervalues():
            cls._expand_ext_cls()

    def _check_main_func(self):
        assert self is main_mod
        main_func = self.func_map.get("main")
        if main_func is None:
            swc_util.exit("主模块‘%s’没有main函数" % self)
        if not main_func.is_public:
            swc_util.exit("主模块‘%s’的main函数必须是public的" % self)
        if len(main_func.arg_map) != 0:
            swc_util.exit("主模块‘%s’的main函数不能有参数" % self)

    def get_main_func(self):
        assert self is main_mod
        return self.func_map["main"]

    def _compile(self):
        for elem in self.iter_mod_elems():
            elem._compile()

    def def_func_obj(self, func_obj):
        self.gfo_list.append(func_obj)

def check_lv_name_conflict(name, t, mod):
    if name in mod.dep_mod_set:
        t.syntax_err("‘%s’和导入模块的名字冲突" % (name))
    if name in mod.name_set():
        t.syntax_err("‘%s’和‘%s.%s’名字冲突" % (name, self, name))
    builtins_name_set = set() if (builtins_mod is None or mod is builtins_mod) else builtins_mod.public_name_set()
    if name in builtins_name_set:
        t.warn("‘%s’在所在函数或方法中隐藏了同名内建元素" % name)

#swarm的函数对象比较简单统一，没必要和模块有从属关系，独立出来

class _FuncObj:
    def __init__(self, mod, func_token, arg_map, tp):
        self.id = swc_util.new_id()

        self.mod        = mod
        self.func_token = func_token
        self.arg_map    = arg_map
        self.stmt_list  = None
        self.tp         = tp

    __repr__ = __str__ = lambda self: "func_obj[%s:%s:%s:%s]" % (self.mod, os.path.basename(self.func_token.src_fn),
                                                                 self.func_token.line_idx + 1, self.func_token.pos + 1)

func_obj_arg_count_set = set(xrange(0, 5))  #0到4个参数是默认有的，可用于Native代码直接使用，其他的在编译期间添加

def parse_func_obj(func_token, token_list, mod, cls, var_map_stk):
    assert func_token.is_reserved("func")

    token_list.pop_sym("(")
    arg_map = _parse_arg_map(token_list)
    for name, tp in arg_map.iteritems():
        check_lv_name_conflict(name, tp.token, mod)

    tp = swc_type.parse_type(func_token, token_list)

    func_obj = _FuncObj(mod, func_token, arg_map, tp)

    token_list.pop_sym("{")
    func_obj.stmt_list = swc_stmt.Parser(token_list, mod, cls, func_obj).parse(var_map_stk + (arg_map.copy(),), 0)
    token_list.pop_sym("}")

    func_obj_arg_count_set.add(len(arg_map))

    return func_obj
