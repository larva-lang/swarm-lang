public class list
{
    !<<
    v   []sw_obj
    !>>

    //todo

    public func size()
    {
        !<<
        return sw_int_from_go_int(int64(len(this.v)))
        !>>
    }

    public func append(e)
    {
        !<<
        this.v = append(this.v, l_e)
        !>>
        return this;
    }
}
