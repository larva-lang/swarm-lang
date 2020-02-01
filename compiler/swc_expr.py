#coding=utf8

import swc_util

class _VarDef:
    def __init__(self, vd, mod):
        self.vd     = vd
        self.mod    = mod

    def name_iter(self):
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
