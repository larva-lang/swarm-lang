import time;

class Record
{
    var ptr_comp,
        discr       int,
        enum_comp   int,
        int_comp    int,
        str_comp,
    ;

    func __init__()
    {
    }

    func assign(other)
    {
        this.ptr_comp   = other.ptr_comp;
        this.discr      = other.discr.int;
        this.enum_comp  = other.enum_comp.int;
        this.int_comp   = other.int_comp.int;
        this.str_comp   = other.str_comp;
    }
}

final var
    IDENT_0 int = 0,
    IDENT_1 int = 1,
    IDENT_2 int = 2,
    IDENT_3 int = 3,
    IDENT_4 int = 4,
    IDENT_5 int = 5,
;

final var LOOPS int = 5000000;

var int_glob    int,
    bool_glob   bool,
    char_1_glob int,
    char_2_glob int,
;
var array_1_glob = [0].repeat(51),
    array_2_glob = map(range(0, 51), func (i int) {
        return [0].repeat(51);
    }),
;
var ptr_glob = Record(),
    ptr_glob_next = Record(),
;

func func_3(enum_par_in int) bool
{
    var enum_loc = enum_par_in;
    if (enum_loc == IDENT_3)
    {
        return true;
    }
    else
    {
        return false;
    }
}

func func_2(str_par_1, str_par_2) bool
{
    var int_loc = 1,
        char_loc = 0;
    while (int_loc <= 1)
    {
        if (func_1(str_par_1.char_at(int_loc).int, str_par_2.char_at(int_loc + 1).int) == IDENT_1)
        {
            char_loc = 'A';
            int_loc = int_loc + 1;
        }
    }
    if (char_loc >= 'W' && char_loc <= 'Z')
    {
        int_loc = 7;
    }
    if (char_loc == 'X')
    {
        return true;
    }
    else
    {
        if (str_par_1.cmp(str_par_2).int > 0)
        {
            int_loc = int_loc + 7;
            return true;
        }
        else
        {
            return false;
        }
    }
}

func func_1(char_par_1 int, char_par_2 int) int
{
    var char_loc_1 = char_par_1,
        char_loc_2 = char_loc_1;
    if (char_loc_2 != char_par_2)
    {
        return IDENT_1;
    }
    else
    {
        return IDENT_2;
    }
}

func proc_8(array_1_par, array_2_par, int_par_1 int, int_par_2 int)
{
    var int_loc = int_par_1 + 5;
    array_1_par.set(int_loc, int_par_2);
    array_1_par.set(int_loc + 1, array_1_par.get(int_loc));
    array_1_par.set(int_loc + 30, int_loc);
    for (var int_idx int: range(int_loc, int_loc + 2))
    {
        array_2_par.get(int_loc).set(int_idx, int_loc);
    }
    array_2_par.get(int_loc).set(int_loc - 1, array_2_par.get(int_loc).get(int_loc - 1).int + 1);
    array_2_par.get(int_loc + 20).set(int_loc, array_1_par.get(int_loc));
    int_glob = 5;
}

func proc_7(int_par_1 int, int_par_2 int) int
{
    var int_loc = int_par_1 + 2,
        int_par_out = int_par_2 + int_loc,
    ;
    return int_par_out;
}

func proc_6(enum_par_in int) int
{
    var enum_par_out = enum_par_in;
    if (!func_3(enum_par_in))
    {
        enum_par_out = IDENT_4;
    }
    if (enum_par_in != IDENT_1)
    {
        enum_par_out = IDENT_1;
    }
    else if (enum_par_in == IDENT_2)
    {
        if (int_glob > 100)
        {
            enum_par_out = IDENT_1;
        }
        else
        {
            enum_par_out = IDENT_4;
        }
    }
    else if (enum_par_in == IDENT_3)
    {
        enum_par_out = IDENT_2;
    }
    else if (enum_par_in == IDENT_4)
    {
    }
    else if (enum_par_in == IDENT_5)
    {
        enum_par_out = IDENT_3;
    }
    return enum_par_out;
}

func proc_5()
{
    char_1_glob = 'A';
    bool_glob = false;
}

func proc_4()
{
    var bool_loc = char_1_glob == 'A';
    bool_loc = bool_loc || bool_glob;
    char_2_glob = 'B';
}

func proc_3(ptr_par_out)
{
    if (ptr_glob !== nil)
    {
        ptr_par_out = ptr_glob.ptr_comp;
    }
    else
    {
        int_glob = 100;
    }
    ptr_glob.int_comp = int_obj(proc_7(10, int_glob));
    return ptr_par_out;
}

func proc_2(int_ptr_io int) int
{
    var int_loc = int_ptr_io + 10,
        enum_loc = IDENT_0,
    ;
    while (true)
    {
        if (char_1_glob == 'A')
        {
            int_loc = int_loc - 1;
            int_ptr_io = int_loc - int_glob;
            enum_loc = IDENT_1;
        }
        if (enum_loc == IDENT_1)
        {
            break;
        }
    }
    return int_ptr_io;
}

func proc_1(ptr_par_in)
{
    var next_record = ptr_par_in.ptr_comp;
    next_record.assign(ptr_glob);

    ptr_par_in.int_comp     = int_obj(5);
    next_record.int_comp    = ptr_par_in.int_comp;
    next_record.ptr_comp    = ptr_par_in.ptr_comp;
    next_record.ptr_comp    = proc_3(next_record.ptr_comp);

    if (next_record.discr.int == IDENT_1)
    {
        next_record.int_comp    = int_obj(6);
        next_record.enum_comp   = int_obj(proc_6(ptr_par_in.enum_comp.int));
        next_record.ptr_comp    = ptr_glob.ptr_comp;
        next_record.int_comp    = int_obj(proc_7(next_record.int_comp.int, 10));
    }
    else
    {
        ptr_par_in.assign(next_record);
    }
    return ptr_par_in;
}

func proc_0()
{
    ptr_glob.ptr_comp   = ptr_glob_next;
    ptr_glob.discr      = int_obj(IDENT_1);
    ptr_glob.enum_comp  = int_obj(IDENT_3);
    ptr_glob.int_comp   = int_obj(40);
    ptr_glob.str_comp   = "DHRYSTONE PROGRAM, SOME STRING";

    var str_1_loc = "DHRYSTONE PROGRAM, 1'ST STRING";

    array_2_glob.get(8).set(7, 10);

    for (var i int: range(0, LOOPS))
    {
        proc_5();
        proc_4();

        var int_loc_1 = 2,
            int_loc_2 = 3,
            str_2_loc = "DHRYSTONE PROGRAM, 2'ND STRING",
            enum_loc = IDENT_2,
        ;

        bool_glob = !func_2(str_1_loc, str_2_loc);

        var int_loc_3 = 0;
        while (int_loc_1 < int_loc_2)
        {
            int_loc_3 = 5 * int_loc_1 - int_loc_2;
            int_loc_3 = proc_7(int_loc_1, int_loc_2);
            int_loc_1 = int_loc_1 + 1;
        }
        proc_8(array_1_glob, array_2_glob, int_loc_1, int_loc_3);
        proc_1(ptr_glob);

        for (var char_idx int: range('A', char_2_glob + 1))
        {
            if (enum_loc == func_1(char_idx, 'C'))
            {
                enum_loc = proc_6(IDENT_1);
            }
        }
        int_loc_3 = int_loc_2 * int_loc_1;
        int_loc_2 = int_loc_3 / int_loc_1;
        int_loc_2 = 7 * (int_loc_3 - int_loc_2) - int_loc_1;
        int_loc_1 = proc_2(int_loc_1);
    }
}

public func main()
{
    var ts = time.time();
    proc_0();
    var tm = time.time().sub(ts);
    println("Time used: %s sec".(tm));
    println("This machine benchmarks at %s SwarmStones/second".(float(int_obj(LOOPS)).div(tm)));
}
