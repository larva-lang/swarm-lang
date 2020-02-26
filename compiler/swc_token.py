#coding=utf8

import re, math, copy

import swc_util

#用于解析token的正则表达式
_TOKEN_RE = re.compile(
    #浮点数
    r"""(\d+\.?\d*[eE][+-]?\w+|"""
    r"""\.\d+[eE][+-]?\w+|"""
    r"""\d+\.\w*|"""
    r"""\.\d\w*)|"""
    #十六进制浮点数
    r"""(0[xX][0-9A-Fa-f]+\.?[0-9A-Fa-f]*[pP][+-]?\w+|"""
    r"""0[xX]\.[0-9A-Fa-f]+[pP][+-]?\w+|"""
    r"""0[xX][0-9A-Fa-f]+\.\w*|"""
    r"""0[xX]\.[0-9A-Fa-f]\w*)|"""
    #符号
    r"""(!=|==|<<=|<<|<=|>>=|>>|>=|[-%^&*+|/]=|&&|\|\||\W)|"""
    #整数
    r"""(\d\w*)|"""
    #词，关键字或标识符
    r"""([a-zA-Z_]\w*)""")

BINOCULAR_OP_SYM_SET = set(["%", "^", "&", "*", "-", "+", "|", "<", ">", "/", "!=", "==", "!==", "===", "<<", "<=", ">>", ">=", "&&", "||"])

#合法的符号集
_SYM_SET = set("""~!()={}[]:;'",.""") | BINOCULAR_OP_SYM_SET

_RESERVED_WORD_SET = set(["import", "class", "func", "for", "while", "if", "else", "return", "nil", "break", "continue", "this", "public",
                          "var", "defer", "final", "isinstanceof", "int"])

class _Token:
    def __init__(self, type, value, src_fn, line_idx, pos):
        self.id = swc_util.new_id()

        self.type = type
        self.value = value
        self.src_fn = src_fn
        self.line_idx = line_idx
        self.pos = pos

        self._set_is_XXX()

        if self.is_literal("str"):
            #字符串字面量的value改为list，方便合并连续的字符串字面量
            assert isinstance(self.value, str)
            self.value = [self.value]

        self._freeze()

    def _freeze(self):
        self.is_freezed = True

    def _unfreeze(self):
        assert self.is_freezed
        del self.__dict__["is_freezed"]

    def _set_is_XXX(self):
        """设置各种is_XXX属性
           如果实现为方法，可能会因偶尔的手误导致莫名其妙的错误，比如：if token.is_literal()写成了if token.is_literal，导致bug
           这里实现为属性，规避下风险，且literal、sym等词法元素的判断实现为方法和属性都可以，即：token.is_sym和token.is_sym(sym)都可以工作"""

        class IsLiteral:
            def __init__(self, token):
                self.token = token
            def __nonzero__(self):
                return self.token.type.startswith("literal_")
            def __call__(self, type):
                assert type in ("nil", "int", "float", "str")
                return self and self.token.type == "literal_" + type
        self.is_literal = IsLiteral(self)

        class IsSym:
            def __init__(self, token):
                self.token = token
            def __nonzero__(self):
                return self.token.type == "sym"
            def __call__(self, sym):
                assert sym in _SYM_SET
                return self and self.token.value == sym
        self.is_sym = IsSym(self)

        class IsReserved:
            def __init__(self, token):
                self.token = token
            def __nonzero__(self):
                return self.token.type == "word" and self.token.value in _RESERVED_WORD_SET
            def __call__(self, word):
                assert word in _RESERVED_WORD_SET, str(word)
                return self and self.token.value == word
        self.is_reserved = IsReserved(self)
        self.is_name = self.type == "word" and self.value not in _RESERVED_WORD_SET

        self.is_native_code = self.type == "native_code"

    __repr__ = __str__ = lambda self: """<Token %r, %d, %d, %r>""" % (self.src_fn, self.line_idx + 1, self.pos + 1, self.value)

    def __setattr__(self, name, value):
        if self.__dict__.get("is_freezed", False):
            swc_util.abort()
        self.__dict__[name] = value

    def __delattr__(self, name):
        if self.__dict__.get("is_freezed", False):
            swc_util.abort()
        del self.__dict__[name]

    def syntax_err(self, msg = ""):
        swc_util.exit("%s %s" % (self.pos_desc(), msg))

    def warn(self, msg):
        swc_util.warn("%s %s" % (self.pos_desc(), msg))

    def pos_desc(self):
        return _pos_desc(self)

class _TokenList:
    def __init__(self, src_fn):
        self.src_fn = src_fn
        self.l = []
        self.i = 0

    def __nonzero__(self):
        return self.i < len(self.l)

    def __iter__(self):
        for i in xrange(self.i, len(self.l)):
            yield self.l[i]

    def copy(self):
        return copy.deepcopy(self)

    def extend(self, other):
        assert self.i == 0 and other.i == 0
        self.l += other.l

    def peek(self, start_idx = 0):
        try:
            return self.l[self.i + start_idx]
        except IndexError:
            swc_util.exit("文件[%s]代码意外结束" % self.src_fn)

    def peek_name(self):
        t = self.peek()
        if not t.is_name:
            t.syntax_err("需要标识符")
        return t.value

    def revert(self, i = None):
        if i is None:
            assert self.i > 0
            self.i -= 1
        else:
            assert 0 <= i <= self.i < len(self.l)
            self.i = i

    def pop(self):
        t = self.peek()
        self.i += 1
        return t

    def pop_sym(self, sym = None):
        t = self.pop()
        if not t.is_sym:
            if sym is None:
                t.syntax_err("需要符号")
            else:
                t.syntax_err("需要符号‘%s’" % sym)
        if sym is None:
            return t, t.value
        if t.value != sym:
            t.syntax_err("需要‘%s’" % sym)
        return t

    def pop_name(self):
        t = self.pop()
        if not t.is_name:
            t.syntax_err("需要标识符")
        return t, t.value

    def _append(self, t):
        assert isinstance(t, _Token)
        if t.is_literal("str") and self.l:
            last_t = self.l[-1]
            if last_t.is_literal("str"):
                #合并连续的字符串字面量
                last_t.value += t.value
                t = self.l.pop()
                assert t is last_t
        self.l.append(t)

    def _join_str_literal(self):
        #合并同表达式中相邻的字符串，即"abc""def""123"合并为"abcdef123"
        for t in self.l:
            if t.is_literal("str"):
                assert isinstance(t.value, list)
                t._unfreeze()
                t.value = "".join(t.value)
                t._freeze()

def _pos_desc(obj):
    return "文件[%s]行[%d]列[%d]" % (obj.src_fn, obj.line_idx + 1, obj.pos + 1)

def _syntax_err(obj, msg):
    swc_util.exit("%s %s" % (_pos_desc(obj), msg))

def _syntax_warn(obj, msg):
    swc_util.warn("%s %s" % (_pos_desc(obj), msg))

class Parser:
    def __init__(self, src_fn):
        self.src_fn = src_fn
        self.line_idx = None
        self.line = None
        self.pos = None

    def _get_escape_char(self, s):
        if s[0] in "abfnrtv":
            #特殊符号转义
            return eval("'\\" + s[0] + "'"), 1

        if s[0] in ("\\", "'", '"'):
            #斜杠和引号转义
            return s[0], 1

        if s[0] >= "0" and s[0] <= "7":
            #八进制换码序列，1到3位数字
            for k in s[: 3], s[: 2], s[0]:
                try:
                    i = int(k, 8)
                    break
                except ValueError:
                    pass
            if i > 255:
                _syntax_err(self, "八进制换码序列值过大[\\%s]" % k)
            return chr(i), len(k)

        if s[0] == "x":
            #十六进制换码序列，两位HH
            if len(s) < 3:
                _syntax_err(self, "十六进制换码序列长度不够")
            try:
                i = int(s[1 : 3], 16)
            except ValueError:
                _syntax_err(self, "十六进制换码序列值错误[\\%s]" % s[: 3])
            return chr(i), 3

        _syntax_err(self, "非法的转义字符[%s]" % s[0])

    def _parse_str(self, s):
        #解析代码中的字符串
        quota = s[0]
        s = s[1 :]
        self.pos += 1

        l = [] #字符列表

        while s:
            c = s[0]
            s = s[1 :]
            self.pos += 1
            if c == quota:
                break
            if c == "\\":
                #转义字符
                if s == "":
                    _syntax_err(self, "字符或字符串字面量在转义处结束")
                c, consume_len = self._get_escape_char(s)
                s = s[consume_len :]
                self.pos += consume_len
            l.append(c) #添加到列表
        else:
            _syntax_err(self, "字符或字符串字面量不完整")

        return "".join(l)

    def _parse_token(self):
        token_pos = self.pos
        s = self.line[token_pos :]
        m = _TOKEN_RE.match(s)
        if m is None:
            _syntax_err(self, "词法错误")

        assert m.start() == 0 and m.end() > 0
        next_pos = self.pos + m.end()

        f, hex_f, sym, i, w = m.groups()

        try:
            if f is not None or hex_f is not None:
                #浮点数
                if f is None:
                    f = hex_f

                try:
                    value = float(f) if hex_f is None else float.fromhex(f)
                    if math.isnan(value) or math.isinf(value):
                        raise ValueError
                except ValueError:
                    _syntax_err(self, "非法的浮点字面量‘%s’" % f)
                return _Token("literal_float", value, self.src_fn, self.line_idx, token_pos)

            if sym is not None:
                #符号
                if sym not in _SYM_SET:
                    _syntax_err(self, "非法的符号%r" % sym)

                if sym in ("'", '"'):
                    #字符或字符串，单独解析，并会自行调整pos
                    value = self._parse_str(s)
                    if sym == "'":
                        if len(value) != 1:
                            _syntax_err(self, "字符字面量必须包含一个字符")
                        return _Token("literal_int", ord(value), self.src_fn, self.line_idx, token_pos)
                    return _Token("literal_str", value, self.src_fn, self.line_idx, token_pos)

                #普通符号token
                return _Token("sym", sym, self.src_fn, self.line_idx, token_pos)

            if i is not None:
                #整数
                try:
                    if i[0] == "0" and len(i) > 1:
                        if i[: 2] in ("0x", "0X"):
                            base = 16
                            prefix_len = 2
                        elif i[: 2] in ("0o", "0O"):
                            base = 8
                            prefix_len = 2
                        elif i[: 2] in ("0b", "0B"):
                            base = 2
                            prefix_len = 2
                        else:
                            base = 8
                            prefix_len = 1
                        value = int(i[prefix_len :], base)
                        #非十进制的int字面量可表示uint64范围，但最终输出的值还是负数
                        if value >= 2 ** 64:
                            _syntax_err(self, "过大的%d进制int字面量‘%s’" % (base, i))
                        if value >= 2 ** 63:
                            value -= 2 ** 64
                    else:
                        value = int(i, 10)
                        if value >= 2 ** 63:
                            _syntax_err(self, "过大的10进制int字面量‘%s’" % i)
                except ValueError:
                    _syntax_err(self, "非法的整数字面量‘%s’" % i)
                return _Token("literal_int", value, self.src_fn, self.line_idx, token_pos)

            if w is not None:
                if w == "nil":
                    return _Token("literal_nil", w, self.src_fn, self.line_idx, token_pos)
                return _Token("word", w, self.src_fn, self.line_idx, token_pos)

        finally:
            if self.pos == token_pos:
                self.pos = next_pos

        swc_util.abort()

    def _parse_line(self):
        token_list = [] #因为是临时解析的一个token列表，需要做分析合并等操作，简单起见直接用list
        uncompleted_comment_start_pos = None
        raw_str = None

        #解析当前行token
        while self.pos < len(self.line):
            #跳过空格
            while self.pos < len(self.line) and self.line[self.pos] in "\t\x20":
                self.pos += 1
            if self.pos >= len(self.line):
                #行结束
                break

            if self.line[self.pos : self.pos + 2] == "//":
                #单行注释，略过本行
                break
            if self.line[self.pos : self.pos + 2] == "/*":
                #块注释
                self.pos += 2
                comment_end_pos = self.line[self.pos :].find("*/")
                if comment_end_pos < 0:
                    #注释跨行了，设置标记略过本行
                    uncompleted_comment_start_pos = self.pos - 2
                    break
                #注释在本行结束，跳过它
                self.pos += comment_end_pos + 2
                continue
            if self.line[self.pos] == "`":
                #原始字符串
                raw_str = _RawStr("", self.src_fn, self.line_idx, self.pos)
                self.pos += 1
                raw_str_end_pos = self.line[self.pos :].find("`")
                if raw_str_end_pos < 0:
                    #跨行了，追加内容并进行下一行
                    raw_str.value += self.line[self.pos :] + "\n"
                    break
                #在本行结束
                raw_str.value += self.line[self.pos : self.pos + raw_str_end_pos]
                raw_str.check()
                token_list.append(_Token("literal_str", raw_str.value, raw_str.src_fn, raw_str.line_idx, raw_str.pos))
                self.pos += raw_str_end_pos + 1
                raw_str = None
                continue

            #解析token
            token = self._parse_token()
            token_list.append(token)

        return token_list, uncompleted_comment_start_pos, raw_str

    def parse(self):
        line_list = swc_util.open_src_file(self.src_fn).read().splitlines()

        token_list = _TokenList(self.src_fn)
        in_comment = False
        raw_str = None
        native_code = None
        for self.line_idx, self.line in enumerate(line_list):
            for self.pos, c in enumerate(self.line):
                assert c not in ("\r", "\n")
                if ord(c) < 32 and c not in ("\t",):
                    _syntax_err(self, "含有非法的ascii控制码‘%r’" % c)
            self.pos = 0

            if in_comment:
                #有未完的注释
                pos = self.line.find("*/")
                if pos < 0:
                    #整行都是注释，忽略
                    continue
                self.pos = pos + 2
                in_comment = False
            elif raw_str is not None:
                #有未完的原始字符串
                pos = self.line.find("`")
                if pos < 0:
                    #整行都是字符串内容，追加
                    raw_str.value += self.line + "\n"
                    continue
                #在本行结束
                raw_str.value += self.line[: pos]
                raw_str.check()
                token_list._append(_Token("literal_str", raw_str.value, raw_str.src_fn, raw_str.line_idx, raw_str.pos))
                self.pos = pos + 1
                raw_str = None
            elif native_code is not None:
                if self.line.strip() == "!>>":
                    #native code结束
                    token_list._append(_Token("native_code", native_code.line_list, native_code.src_fn, native_code.line_idx, native_code.pos))
                    native_code = None
                else:
                    native_code.line_list.append(self.line)
                    if self.line.rstrip().endswith(";"):
                        _syntax_warn(self, "Native代码行以分号结尾")
                continue
            else:
                if self.line.strip() == "!<<":
                    #native code开始
                    native_code = _NativeCode(self.src_fn, self.line_idx, self.line.find("!<<"))
                    continue

            line_tl, uncompleted_comment_start_pos, raw_str = self._parse_line()
            for t in line_tl:
                token_list._append(t)
            if uncompleted_comment_start_pos is not None:
                assert raw_str is None
                in_comment = True

        self.line_idx, self.pos = len(line_list), (len(line_list[-1]) if line_list else 0)
        if in_comment:
            _syntax_err(self, "存在未结束的块注释")
        if raw_str is not None:
            _syntax_err(self, "存在未结束的原始字符串")
        if native_code is not None:
            _syntax_err(self, "存在未结束的native code")

        token_list._join_str_literal()

        return token_list

class _RawStr:
    def __init__(self, value, src_fn, line_idx, pos):
        self.value = value
        self.src_fn = src_fn
        self.line_idx = line_idx
        self.pos = pos

    def check(self):
        if "\t\n" in self.value or "\x20\n" in self.value:
            _syntax_warn(self, "原始字符串含有空格或制表符结尾的行")

class _NativeCode:
    def __init__(self, src_fn, line_idx, pos):
        self.src_fn = src_fn
        self.line_idx = line_idx
        self.pos = pos
        self.line_list = []

def is_valid_name(name):
    return re.match("^[a-zA-Z_]\w*$", name) is not None and name not in _RESERVED_WORD_SET

def parse_token_list_until_sym(token_list, end_sym_set):
    bracket_map = {"(" : ")", "[" : "]", "{" : "}"}
    sub_token_list = _TokenList(token_list.src_fn)
    stk = []
    while True:
        t = token_list.pop()
        sub_token_list._append(t)
        if t.is_sym and t.value in end_sym_set and not stk:
            return sub_token_list, t.value
        if t.is_sym and t.value in bracket_map:
            stk.append(t)
        if t.is_sym and t.value in bracket_map.values():
            if not (stk and stk[-1].is_sym and t.value == bracket_map.get(stk[-1].value)):
                t.syntax_err("未匹配的'%s'" % t.value)
            stk.pop()
