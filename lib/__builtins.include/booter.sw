!<<

func sw_booter_output_unhandled_exc(c *sw_exc_stru_catched) {
    fmt.Fprintln(os.Stderr, c.tb)
}

func sw_booter_check_go_panic() {
    r := recover()
    if r != nil {
        fmt.Fprintln(os.Stderr, "process crash:", r)
        fmt.Fprintln(os.Stderr, "traceback:")
        fmt.Fprintln(os.Stderr, sw_exc_create_catched(nil, 0).tb)
        panic(r)
    }
}

func sw_booter_start_prog(init_std_lib_internal_mods func (), main_mod_init_func func (), main_func func () sw_obj) {
    exit_code := 0
    defer func () {
        if r := recover(); r != nil {
            panic(r)
        }
        os.Exit(exit_code)
    }()

    defer sw_booter_check_go_panic()
    defer func () {
        c := sw_exc_recovered_to_catched(recover())
        if c != nil {
            sw_booter_output_unhandled_exc(c)
            exit_code = 2
        }
    }()

    init_std_lib_internal_mods()
    main_mod_init_func()
    main_func()
}

//这个先做一个简单的
func sw_booter_start_fiber(f sw_obj) {
    defer sw_booter_check_go_panic()
    defer func () {
        c := sw_exc_recovered_to_catched(recover())
        if c != nil {
            sw_booter_output_unhandled_exc(c)
        }
    }()

    f.sw_method_call(-1)
}

!>>
