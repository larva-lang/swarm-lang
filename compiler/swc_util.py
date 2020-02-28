#coding=utf8

import time, sys, os

_vmode = False

def enable_vmode():
    global _vmode
    _vmode = True

def vlog(msg):
    if _vmode:
        print time.strftime("swc: [%H:%M:%S]"), msg

def exit(msg):
    print >> sys.stderr, "错误：" + msg
    sys.exit(1)

def warn(msg):
    print >> sys.stderr, "警告：" + msg

def abort():
    raise Exception("swc abort")

class OrderedDict:
    def __init__(self):
        self.l = []
        self.d = {}

    def __iter__(self):
        return iter(self.l)

    def __contains__(self, x):
        return x in self.d

    def __len__(self):
        return len(self.l)

    def __nonzero__(self):
        return len(self) > 0

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        if k not in self.d:
            self.l.append(k)
        self.d[k] = v

    def get(self, k, default = None):
        return self.d.get(k, default)

    def itervalues(self):
        for k in self.l:
            yield self.d[k]

    def iteritems(self):
        for k in self.l:
            yield k, self.d[k]

    def key_at(self, idx):
        return self.l[idx]

    def value_at(self, idx):
        return self.d[self.l[idx]]

    def copy(self):
        od = OrderedDict()
        for name in self:
            od[name] = self[name]
        return od

class OrderedSet:
    def __init__(self):
        self.d = OrderedDict()

    def __contains__(self, x):
        return x in self.d

    def __iter__(self):
        return iter(self.d)

    def __len__(self):
        return len(self.d)

    def __nonzero__(self):
        return len(self) > 0

    def add(self, k):
        self.d[k] = None

    def elem_at(self, idx):
        return self.d.key_at(idx)

    def copy(self):
        os = OrderedSet()
        os.d = self.d.copy()
        return os

_id = 0
def new_id():
    global _id
    _id += 1
    return _id

def open_src_file(fn):
    f = open(fn)
    f.seek(0, os.SEEK_END)
    if f.tell() > 1024 ** 2:
        exit("源代码文件[%s]过大" % fn)
    f.seek(0, os.SEEK_SET)
    f_cont = f.read()
    try:
        f_cont.decode("utf8")
    except UnicodeDecodeError:
        exit("源代码文件[%s]不是utf8编码" % fn)
    if "\r" in f_cont:
        warn("源代码文件[%s]含有回车符‘\\r’" % fn)
    f.seek(0, os.SEEK_SET)
    return f

#解析逗号分隔的items，以end_sym结束
def parse_items(token_list, parse_single_item, end_sym):
    while True:
        parse_single_item()
        #以end_sym结尾，或者逗号+end_sym结尾，都是正常结束，只有逗号则继续下一个item
        t, sym = token_list.pop_sym()
        if sym == end_sym:
            return
        if sym != ",":
            t.syntax_err("需要‘%s’或‘,’" % end_sym)
        if token_list.peek().is_sym(end_sym):
            token_list.pop_sym(end_sym)
            return

class Freezable:
    def _freeze(self):
        self._is_freezed = True

    def _unfreeze(self):
        assert self._is_freezed
        del self.__dict__["_is_freezed"]

    def __setattr__(self, name, value):
        if self.__dict__.get("_is_freezed", False):
            swc_util.abort()
        self.__dict__[name] = value

    def __delattr__(self, name):
        if self.__dict__.get("_is_freezed", False):
            swc_util.abort()
        del self.__dict__[name]
