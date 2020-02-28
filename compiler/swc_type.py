#coding=utf8

import swc_util

class Type(swc_util.Freezable):
    def __init__(self, t, is_int):
        self.token  = t
        self.is_int = is_int

        self._freeze()
