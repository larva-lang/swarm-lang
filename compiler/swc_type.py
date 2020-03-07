#coding=utf8

import swc_util

class _Type(swc_util.Freezable):
    def __init__(self, t, is_int, is_bool):
        assert not (is_int and is_bool)

        self.token  = t
        self.is_int = 1 if is_int else 0
        self.is_bool = 1 if is_bool else 0
        self.is_obj = 1 if (not (is_int or is_bool)) else 0

        self._freeze()

    __str__ = __repr__ = lambda self: "int" if self.is_int else ("bool" if self.is_bool else "对象")

    def __eq__(self, other):
        for tp_name in "int", "bool":
            attr_name = "is_" + tp_name
            if getattr(self, attr_name) != getattr(other, attr_name):
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def to_bool_type(self):
        return make_bool_type(self.token)

    def to_int_type(self):
        return make_int_type(self.token)

    def to_obj_type(self):
        return make_obj_type(self.token)

    def to_other_type(self, other):
        return _Type(self.token, other.is_int, other.is_bool)

def parse_type(name_t, token_list):
    t = token_list.peek()
    is_bool = t.is_reserved("bool")
    is_int = t.is_reserved("int")
    if is_bool or is_int:
        token_list.pop()
    else:
        t = name_t
    return _Type(t, is_int, is_bool)

def make_bool_type(t):
    return _Type(t, False, True)

def make_int_type(t):
    return _Type(t, True, False)

def make_obj_type(t):
    return _Type(t, False, False)

def make_type_from_cls(cls):
    assert cls.is_cls
    return _Type(cls.name_token, False, False)
