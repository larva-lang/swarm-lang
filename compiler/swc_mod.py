#coding=utf8

import os

import swc_util, swc_token

mod_path = None

def find_mod_file(mod_name):
    for d in mod_path:
        mod_fn = "%s/%s.sw" % (d, mod_name)
        if os.path.isfile(mod_fn):
            return mod_fn
    swc_util.exit("找不到模块‘%s’" % mod_name)

builtins_mod = None
main_mod = None
mod_map = swc_util.OrderedDict()

def precompile(main_mod_name):
    global builtins_mod, main_mod
    mod_map["__builtins"] = builtins_mod = Mod("__builtins")
    mod_map[main_mod_name] = main_mod = Mod(main_mod_name)

class Mod:
    def __init__(self, mn):
        self.name = mn
        self.src_fn = find_mod_file(self.name)

        self.cls_map = swc_util.OrderedDict()
        self.func_map = swc_util.OrderedDict()
        self.gv_map = swc_util.OrderedDict()
        self.literal_list = []
        self.gnc_list = []

        self._precompile()

    def _precompile(self):
        token_list = swc_token.Parser(self.src_fn).parse()
        self._parse_text(token_list)

    def _parse_text(self, token_list):
        "todo"
        print self.src_fn
        print token_list
