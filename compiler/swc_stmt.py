#coding=utf8

import swc_util, swc_expr

class Parser:
    def __init__(self, token_list, mod, cls, fom):
        self.token_list = token_list
        self.mod        = mod
        self.cls        = cls
        self.fom        = fom

        self.expr_parser = swc_expr.Parser(token_list, mod, cls, fom)

    def parse(self, var_map_stk, loop_deep):
        todo
