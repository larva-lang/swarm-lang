!<<

/*
sw_obj是一个所有对象的句柄类型，是一个interface，包含了程序涉及到的所有可能的方法，因此不能写在代码中，而是由编译器生成在util代码中
*/
//type sw_obj interface {...}

//sw_obj转为go的字符串
func sw_obj_to_go_str(obj sw_obj) string {
    //调用内部方法‘__str__’得到字符串表示，确保是字符串对象，然后转为go的字符串
    s, ok := sw_obj.sw_method___str___0().(*sw_cls_@<<:str>>)
    if !ok {
        sw_func_@<<:throw>>_1(sw_new_obj_@<<:TypeError>>_1(sw_str_from_go_str("‘__str__’方法返回的对象不是字符串")))
    }
    return s.s
}

!>>
