#coding=utf8

import swc_util

class _Type(swc_util.Freezable):
    def __init__(self, t, is_int):
        self.token  = t
        self.is_int = is_int

        self._freeze()

    def __eq__(self, other):
        return (self.is_int and other.is_int) or (not self.is_int and not other.is_int)

    def __ne__(self, other):
        return not (self == other)

    def to_int_type(self):
        return make_int_type(self.token)

    def to_non_int_type(self):
        return make_non_int_type(self.token)

def parse_type(name_t, token_list):
    if token_list.peek().is_reserved("int"):
        t = token_list.pop()
        is_int = True
    else:
        t = name_t
        is_int = False
    return _Type(t, is_int)

def make_int_type(t):
    return _Type(t, True)

def make_non_int_type(t):
    return _Type(t, False)

def make_type_from_cls(cls):
    assert cls.is_cls
    return _Type(cls.name_token, False)
