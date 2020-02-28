#coding=utf8

import swc_util

class _Type(swc_util.Freezable):
    def __init__(self, t, is_int):
        self.token  = t
        self.is_int = is_int

        self._freeze()

    def __eq__(self, other):
        return (self.is_int and other.is_int) or (not self.is_int and not other.is_int)

    def to_int_type(self):
        return _Type(self.token, True)

def parse_type(name_t, token_list):
    if token_list.peek().is_reserved("int"):
        t = token_list.pop()
        is_int = True
    else:
        t = name_t
        is_int = False
    return swc_type._Type(t, is_int)
