#coding=utf8

import sys, getopt, os, shutil

import swc_util, swc_token, swc_mod, swc_out

def main():
    #定位目录
    THIS_SCRIPT_NAME_SUFFIX = "/compiler/swc.py"
    this_script_name = os.path.realpath(sys.argv[0])
    assert this_script_name.endswith(THIS_SCRIPT_NAME_SUFFIX)
    sw_dir = this_script_name[: -len(THIS_SCRIPT_NAME_SUFFIX)]

    #解析命令行参数
    try:
        opt_list, args = getopt.getopt(sys.argv[1 :], "v")
    except getopt.GetoptError:
        _show_usage_and_exit()
    opt_map = dict(opt_list)
    if "-v" in opt_map:
        swc_util.enable_vmode()

    swc_util.vlog("开始")

    #主模块
    assert len(args) == 1
    main_mod_file = args[0]
    assert main_mod_file.endswith(".sw")
    if not os.path.isfile(main_mod_file):
        swc_util.exit("主模块代码‘%s’不是一个文件" % main_mod_file)
    main_mod_name = os.path.basename(main_mod_file)[: -3]
    if not swc_token.is_valid_name(main_mod_name):
        swc_util.exit("主模块名‘%s’不是一个合法标识符" % main_mod_name)

    #模块查找路径
    swc_mod.mod_path = [os.path.dirname(main_mod_file), sw_dir + "/lib"]

    #目标输出路径
    swc_out.out_dir = "%s/tmp/out/%s" % (sw_dir, main_mod_name)

    swc_mod.precompile(main_mod_name)

    #todo

if __name__ == "__main__":
    main()
