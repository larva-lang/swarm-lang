public func throw(exc)
{
    !<<
    panic(sw_exc_create_catched(l_exc, 2))
    !>>
}

public func rethrow(exc, tb)
{
    if (!isinstanceof(tb, str))
    {
        abort("rethrow的tb参数必须是字符串");
    }
    !<<
    panic(&sw_exc_stru_catched{
        exc:    l_exc,
        tb:     l_tb.(*sw_cls_@<<:str>>).v,
    })
    !>>
}

public func handle_exc(handler)
{
    var (exc, tb);

    !<<
    c := sw_exc_recovered_to_catched(recover())

    l_exc   = c.exc
    l_tb    = sw_obj_str_from_go_str(c.tb)
    !>>

    handler.call(exc, tb);
}

public func call_and_catch(f)
{
    var (exc, tb);
    func () {
        defer handle_exc(func (_exc, _tb) {
            exc = _exc;
            tb  = _tb;
        });

        f.call();
    }.call();
    return (exc, tb);
}

!<<

type sw_util_go_tb struct {
    file    string
    line    int
}

type sw_util_sw_tb struct {
    file        string
    line        int
    fom_name    string
}

func sw_util_convert_go_tb_to_sw_tb(file string, line int, func_name string) (string, int, string, bool) {
    sw_tb, ok := sw_util_tb_map[sw_util_go_tb{file: file, line: line}]
    if !ok {
        //没找到对应的，抹掉函数名后返回
        return file, line, "", true
    }
    if sw_tb == nil {
        return "", 0, "", false
    }
    return sw_tb.file, sw_tb.line, sw_tb.fom_name, true
}

var sw_util_GOROOT_path = func () (ret string) {
    //通过回溯调用栈找到reflect库目录，继而解析GOROOT路径，不能用runtime.GOROOT()是因为需要编译时的GOROOT而非运行时的
    reflect.ValueOf(func () {
        sep := string(filepath.Separator)
        reflect_path_suffix := sep + "src" + sep + "reflect"
        for i := 0; true; i ++ {
            _, file, _, ok := runtime.Caller(i)
            if !ok {
                panic("获取编译信息失败：无法获取GOROOT，调用栈中找不到reflect包")
            }
            file_dir := filepath.Dir(file)
            if strings.HasSuffix(file_dir, reflect_path_suffix) {
                ret = file_dir[: len(file_dir) - len(reflect_path_suffix) + 1] //末尾需要保留一个sep
                if ret == sep {
                    panic("获取编译信息失败：GOROOT为空")
                }
                return
            }
        }
    }).Call(nil)
    return
}()

type sw_exc_stru_catched struct {
    exc sw_obj
    tb  string
}

func sw_exc_create_catched(exc sw_obj, skip int) *sw_exc_stru_catched {
    var tb_line_list []string
    if exc != nil {
        tb_line_list = append(tb_line_list, exc.type_name() + ": " + sw_obj_to_go_str(exc))
    }
    for i := skip; true; i ++ {
        pc, file, line, ok := runtime.Caller(i)
        if !ok {
            break
        }
        if file == "<autogenerated>" || strings.HasPrefix(file, sw_util_GOROOT_path) {
            //忽略自动生成文件和go内建库的tb
            continue
        }
        func_name := runtime.FuncForPC(pc).Name()
        in_init_mod_func := false
        func_name_parts := strings.Split(func_name, ".")
        if len(func_name_parts) == 2 {
            fn := func_name_parts[1]
            if fn == "sw_booter_start_prog" || fn == "sw_booter_start_fiber" {
                //追溯到了fiber的入口，停止
                break
            }
            if strings.HasPrefix(fn, "sw_env_init_mod_") {
                in_init_mod_func = true
            }
        }
        file, line, func_name, ok = sw_util_convert_go_tb_to_sw_tb(file, line, func_name)
        if ok {
            if in_init_mod_func && func_name != "<module>" {
                //追溯到了模块初始化代码，且不是swarm层面的代码行，则停止
                break
            }
            tb_line := fmt.Sprintf("  File %q, line %d", file, line)
            if func_name != "" {
                tb_line += ", in " + func_name
            }
            if len(tb_line_list) == 0 || tb_line_list[len(tb_line_list) - 1] != tb_line {
                tb_line_list = append(tb_line_list, tb_line)
            }
        }
    }
    tb_line_list = append(tb_line_list, "Traceback:")

    //上面是反着写info的，reverse一下
    tb_line_count := len(tb_line_list)
    for i := 0; i < tb_line_count / 2; i ++ {
        tb_line_list[i], tb_line_list[tb_line_count - 1 - i] = tb_line_list[tb_line_count - 1 - i], tb_line_list[i]
    }

    return &sw_exc_stru_catched{
        exc:    exc,
        tb:     strings.Join(tb_line_list, "\n"),
    }
}

func sw_exc_recovered_to_catched(r interface{}) *sw_exc_stru_catched {
    if r == nil {
        return nil
    }
    if c, ok := r.(*sw_exc_stru_catched); ok {
        return c
    }
    panic(r)
}

!>>
