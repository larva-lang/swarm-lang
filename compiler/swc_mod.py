#coding=utf8

import os

import swc_util, swc_token, swc_expr

mod_path = None

builtins_mod = None
main_mod = None
mod_map = swc_util.OrderedDict()

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
    while True:
        if token_list.peek().is_sym(")"):
            break
        t, name = token_list.pop_name()
        if name in arg_map:
            t.syntax_err("参数重复定义")
        arg_map[name] = t
        t = token_list.peek()
        if t.is_sym(")"):
            break
        if not t.is_sym(","):
            t.syntax_err("需要‘,’或‘)’")
        token_list.pop()
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

class _NativeCode:
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

class _Attr:
    def __init__(self, cls, decr_set, name_token, name):
        self.cls        = cls
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name

    __repr__ = __str__ = lambda self : "%s.%s" % (self.cls, self.name)

class _Method:
    def __init__(self, cls, decr_set, name_token, name, arg_map, block_token_list):
        self.cls        = cls
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name
        self.arg_map    = arg_map

        self.block_token_list   = block_token_list
        self.stmt_list          = None

    __repr__ = __str__ = lambda self : "%s.%s" % (self.cls, self.name)

    def _compile(self):
        self.stmt_list = swc_stmt.Parser(self.block_token_list, self.cls.mod, self.cls, self).parse((self.arg_map.copy(),), 0) #todo
        self.block_token_list.pop_sym("}")
        assert not self.block_token_list
        del self.block_token_list

class _Cls:
    def __init__(self, mod, decr_set, name_token, name):
        self.mod        = mod
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name

        self.nc_list    = []
        self.attr_map   = swc_util.OrderedDict()
        self.method_map = swc_util.OrderedDict()

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

    def _parse(self, token_list):
        while True:
            t = token_list.peek()
            if t.is_sym("}"):
                break

            if t.is_native_code:
                token_list.pop()
                self.nc_list.append(_NativeCode(self.mod, t))
                continue

            #解析修饰
            decr_set = _parse_decr_set(token_list)
            if decr_set - set(["public"]):
                t.syntax_err("方法或属性只能用public修饰")

            t = token_list.pop()

            if t.is_reserved("var"):
                #属性定义
                while True:
                    t, name = token_list.pop_name()
                    self._check_redefine(t, name)
                    self.attr_map[name] = _Attr(self, decr_set, t, name)
                    t, sym = token_list.pop_sym()
                    if sym == ";":
                        break
                    if sym != ",":
                        t.syntax_err("需要‘,’或‘;’")
                    if token_list.peek().is_sym(";"):
                        token_list.pop()
                        break
                continue

            if t.is_reserved("func"):
                #方法定义
                t, name = token_list.pop_name()
                self._check_redefine(t, name)
                token_list.pop_sym("(")
                arg_map = _parse_arg_map(token_list)
                token_list.pop_sym(")")
                token_list.pop_sym("{")
                block_token_list, sym = swc_token.parse_token_list_until_sym(token_list, ("}",))
                assert sym == "}"
                self.method_map[name] = _Method(self, decr_set, t, name, arg_map, block_token_list)
                continue

            t.syntax_err("需要属性或方法定义")

    def _check_redefine(self, t, name):
        for i in self.attr_map, self.method_map:
            if name in i:
                t.syntax_err("属性或方法名重定义")

    def _compile(self):
        for method in self.method_map.itervalues():
            method._compile()

class _Func:
    def __init__(self, mod, decr_set, name_token, name, arg_map, block_token_list):
        self.mod        = mod
        self.is_public  = "public" in decr_set
        self.name_token = name_token
        self.name       = name
        self.arg_map    = arg_map

        self.block_token_list   = block_token_list
        self.stmt_list          = None

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

    def _compile(self):
        self.stmt_list = swc_stmt.Parser(self.block_token_list, self.mod, None, self).parse((self.arg_map.copy(),), 0) #todo
        self.block_token_list.pop_sym("}")
        assert not self.block_token_list
        del self.block_token_list

class _Gv:
    def __init__(self, mod, decr_set, name_token, name):
        self.mod        = mod
        self.is_public  = "public" in decr_set
        self.is_final   = "final" in decr_set
        self.name_token = name_token
        self.name       = name

    __repr__ = __str__ = lambda self : "%s.%s" % (self.mod, self.name)

class _GvInit:
    def __init__(self, mod, var_def, expr_token_list):
        self.mod        = mod
        self.var_def    = var_def

        self.expr_token_list    = expr_token_list
        self.expr               = None

    def _compile(self):
        self.expr = swc_expr.Parser(self.expr_token_list, self.mod, None, None).parse(())
        self.expr_token_list.pop_sym(";")
        assert not self.expr_token_list
        del self.expr_token_list

class Mod:
    def __init__(self, mn):
        self.name = mn
        self.src_fn = self._find_mod_file()

        self.literal_list   = None
        self.dep_mod_set    = set()
        self.gnc_list       = []
        self.cls_map        = swc_util.OrderedDict()
        self.func_map       = swc_util.OrderedDict()
        self.gv_map         = swc_util.OrderedDict()
        self.gv_init_list   = []

        self._precompile()
        self._check_name_conflict()

    __repr__ = __str__ = lambda self : self.name

    def _find_mod_file(self):
        for d in mod_path:
            mod_fn = "%s/%s.sw" % (d, self.name)
            if os.path.isfile(mod_fn):
                return mod_fn
        swc_util.exit("找不到模块‘%s’" % self.name)

    def _precompile(self):
        token_list = swc_token.Parser(self.src_fn).parse()
        self._parse_text(token_list)

    def _parse_text(self, token_list):
        self.literal_list = [t for t in token_list if t.is_literal]

        import_end = False
        while token_list:
            #解析import
            t = token_list.peek()
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
                self.gnc_list.append(_NativeCode(self, t))
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
        t, name = token_list.pop_name()
        if name in self.dep_mod_set:
            t.syntax_err("模块重复导入")
        if name == "__builtins":
            t.syntax_err("不能显式导入‘__builtins’")
        self.dep_mod_set.add(name)
        token_list.pop_sym(";")

    def _parse_cls(self, decr_set, token_list):
        t, name = token_list.pop_name()
        self._check_redefine(t, name)
        token_list.pop_sym("{")
        cls = _Cls(self, decr_set, t, name)
        cls._parse(token_list)
        token_list.pop_sym("}")
        self.cls_map[name] = cls

    def _parse_func(self, decr_set, token_list):
        t, name = token_list.pop_name()
        self._check_redefine(t, name)
        token_list.pop_sym("(")
        arg_map = _parse_arg_map(token_list)
        token_list.pop_sym(")")
        token_list.pop_sym("{")
        block_token_list, sym = swc_token.parse_token_list_until_sym(token_list, ("}",))
        assert sym == "}"
        self.func_map[name] = _Func(self, decr_set, t, name, arg_map, block_token_list)

    def _parse_gv(self, decr_set, token_list):
        var_def = swc_expr.parse_var_def(token_list)
        for t, name in var_def.iter_names():
            self._check_redefine(t, name)
            self.gv_map[name] = _Gv(self, decr_set, t, name)
        t = token_list.pop()
        if t.is_sym(";"):
            #无初始化
            return
        if not t.is_sym("="):
            t.syntax_err("需要‘;’或‘=’")
        block_token_list, sym = swc_token.parse_token_list_until_sym(token_list, (";",))
        assert sym == ";"
        self.gv_init_list.append(_GvInit(self, var_def, block_token_list))

    def _check_redefine(self, t, name):
        if name in self.dep_mod_set:
            t.syntax_err("定义的名字和导入模块名重名")
        for i in self.cls_map, self.func_map, self.gv_map:
            if name in i:
                t.syntax_err("名字重定义")

    def iter_mod_elems(self):
        for m in self.cls_map, self.func_map, self.gv_map:
            for elem in m.itervalues():
                yield elem

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
            for name, t in arg_map.iteritems():
                if name in self.dep_mod_set:
                    t.syntax_err("参数‘%s’和导入模块的名字冲突" % (name))
                if name in mod_name_set:
                    t.syntax_err("参数‘%s’和‘%s.%s’名字冲突" % (name, self, name))
                if name in builtins_name_set:
                    t.warn("参数‘%s’在所在函数或方法中隐藏了同名内建元素" % name)

    def _check_main_func(self):
        if "main" not in self.func_map:
            swc_util.exit("主模块‘%s’没有main函数" % self)
        main_func = self.func_map["main"]
        if not main_func.is_public:
            swc_util.exit("主模块‘%s’的main函数必须是public的" % self)
        if len(main_func.arg_map) != 0:
            swc_util.exit("主模块‘%s’的main函数不能有参数" % self)

    def _compile(self):
        for m in self.cls_map, self.func_map:
            for elem in m.itervalues():
                elem._compile()
        for gi in self.gv_init_list:
            gi._compile()
