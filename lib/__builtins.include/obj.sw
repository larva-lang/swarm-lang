!<<

/*
sw_obj是一个所有对象的句柄类型，是一个interface，包含了程序涉及到的所有可能的方法，因此不能写在代码中，而是由编译器生成在util代码中
*/
//type sw_obj interface {...}

//sw_obj转为go的字符串
func sw_obj_to_go_str(obj sw_obj) string {
    //直接构造str对象并返回其内部value
    return sw_new_obj_@<<:str>>_1(obj).v
}

!>>
