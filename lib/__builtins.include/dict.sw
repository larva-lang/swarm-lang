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

    public func __init__(kv_it)
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

        if (kv_it !== nil)
        {
            this.update(kv_it);
        }
    }

    public func update(kv_it)
    {
        for (var kv: kv_it)
        {
            var k, v;
            (k, v) = kv;
            this.set(k, v);
        }
        return this;
    }

    public func get(k)
    {
        //todo
        throw(NotImpl());
    }

    public func set(k, v)
    {
        //todo
        throw(NotImpl());
        return this;
    }

    public func reserve_space(sz int)
    {
        //todo
        throw(NotImpl());
        return this;
    }

    //todo
}
