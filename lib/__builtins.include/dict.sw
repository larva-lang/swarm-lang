!<<

type sw_obj_dict_node_stru struct {
    //键值对
    k   sw_obj
    v   sw_obj

    //链表法解决冲突
    next    *sw_obj_dict_node_stru

    //用于维持插入顺序并简化遍历
    prev_node   *sw_obj_dict_node_stru
    next_node   *sw_obj_dict_node_stru
}

!>>

public class dict
{
    !<<
    tbl []*sw_obj_dict_node_stru

    node_head   *sw_obj_dict_node_stru
    node_tail   *sw_obj_dict_node_stru

    sz      int64
    dirty   int64
    !>>

    public func __init__()
    {
        !<<
        this.tbl = make([]*sw_obj_dict_node_stru, 1 << 3)

        this.node_head = &sw_obj_dict_node_stru{}
        this.node_tail = &sw_obj_dict_node_stru{
            prev_node:  this.node_head,
        }
        this.node_head.next_node = this.node_tail

        this.sz     = 0
        this.dirty  = 1
        !>>
    }

    public func __init__(kv_it)
    {
        this.__init__();
        this.update(kv_it);
    }

    public func update(kv_it)
    {
        for (var (k, v): kv_it)
        {
            this[k] = v;
        }
    }

    public func __getelem__(k)
    {
        //todo
    }

    public func __setelem__(k, v)
    {
        //todo
        return this;
    }

    public func reserve_space(sz)
    {
        //todo
        return this;
    }

    //todo
}
