import time;

class Record
{
    var ptr_comp, discr, enum_comp, int_comp, str_comp;

    func assign(other)
    {
        this.ptr_comp   = other.ptr_comp;
        this.discr      = other.discr;
        this.enum_comp  = other.enum_comp;
        this.int_comp   = other.int_comp;
        this.str_comp   = other.str_comp;
    }
}

final var (IDENT_0, IDENT_1, IDENT_2, IDENT_3, IDENT_4, IDENT_5) = (0, 1, 2, 3, 4, 5);
final var LOOPS = 50000000;

var (int_glob, bool_glob, char_1_glob, char_2_glob) = (0, false, 0, 0);
var array_1_glob = [0] * 51;
var array_2_glob = map(range(0, 51), func (i) {
    return [0] * 51;
});
var (ptr_glob, ptr_glob_next) = (Record(), Record());

func func_3(enum_par_in)
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

func func_2(str_par_1, str_par_2)
{
    var (int_loc, char_loc) = (1, 0);
    while (int_loc <= 1)
    {
        if (func_1(str_par_1[int_loc], str_par_2[int_loc + 1]) == IDENT_1)
        {
            char_loc = 65;
            int_loc += 1;
        }
    }
    if (char_loc >= 87 && char_loc <= 90)
    {
        int_loc = 7;
    }
    if (char_loc == 88)
    {
        return true;
    }
    else
    {
        if (str_par_1 > str_par_2)
        {
            int_loc += 7;
            return true;
        }
        else
        {
            return false;
        }
    }
}

func func_1(char_par_1, char_par_2)
{
    var char_loc_1 = char_par_1;
    var char_loc_2 = char_loc_1;
    if (char_loc_2 != char_par_2)
    {
        return IDENT_1;
    }
    else
    {
        return IDENT_2;
    }
}

func proc_8(array_1_par, array_2_par, int_par_1, int_par_2)
{
    var int_loc = int_par_1 + 5;
    array_1_par[int_loc] = int_par_2;
    array_1_par[int_loc + 1] = array_1_par[int_loc];
    array_1_par[int_loc + 30] = int_loc;
    for (var int_idx: range(int_loc, int_loc + 2))
    {
        array_2_par[int_loc][int_idx] = int_loc;
    }
    array_2_par[int_loc][int_loc - 1] += 1;
    array_2_par[int_loc + 20][int_loc] = array_1_par[int_loc];
    int_glob = 5;
}

func proc_7(int_par_1, int_par_2)
{
    var int_loc = int_par_1 + 2;
    var int_par_out = int_par_2 + int_loc;
    return int_par_out;
}

func proc_6(enum_par_in)
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
    char_1_glob = 65;
    bool_glob = false;
}

func proc_4()
{
    var bool_loc = char_1_glob == 65;
    bool_loc = bool_loc || bool_glob;
    char_2_glob = 66;
}

func proc_3(ptr_par_out)
{
    if (!(ptr_glob is nil))
    {
        ptr_par_out = ptr_glob.ptr_comp;
    }
    else
    {
        int_glob = 100;
    }
    ptr_glob.int_comp = proc_7(10, int_glob);
    return ptr_par_out;
}

func proc_2(int_ptr_io)
{
    var int_loc = int_ptr_io + 10;
    var enum_loc = IDENT_0;
    while (true)
    {
        if (char_1_glob == 65)
        {
            int_loc -= 1;
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

    ptr_par_in.int_comp     = 5;
    next_record.int_comp    = ptr_par_in.int_comp;
    next_record.ptr_comp    = ptr_par_in.ptr_comp;
    next_record.ptr_comp    = proc_3(next_record.ptr_comp);

    if (next_record.discr == IDENT_1)
    {
        next_record.int_comp    = 6;
        next_record.enum_comp   = proc_6(ptr_par_in.enum_comp);
        next_record.ptr_comp    = ptr_glob.ptr_comp;
        next_record.int_comp    = proc_7(next_record.int_comp, 10);
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
    ptr_glob.discr      = IDENT_1;
    ptr_glob.enum_comp  = IDENT_3;
    ptr_glob.int_comp   = 40;
    ptr_glob.str_comp   = "DHRYSTONE PROGRAM, SOME STRING";

    var str_1_loc = "DHRYSTONE PROGRAM, 1'ST STRING";

    array_2_glob[8][7] = 10;

    for (var i: range(0, LOOPS))
    {
        proc_5();
        proc_4();

        var (int_loc_1, int_loc_2, str_2_loc, enum_loc) = (2, 3, "DHRYSTONE PROGRAM, 2'ND STRING", IDENT_2);

        bool_glob = !func_2(str_1_loc, str_2_loc);

        var int_loc_3 = 0;
        while (int_loc_1 < int_loc_2)
        {
            int_loc_3 = 5 * int_loc_1 - int_loc_2;
            int_loc_3 = proc_7(int_loc_1, int_loc_2);
            int_loc_1 += 1;
        }
        proc_8(array_1_glob, array_2_glob, int_loc_1, int_loc_3);
        proc_1(ptr_glob);

        for (var char_idx: range(65, char_2_glob + 1))
        {
            if (enum_loc == func_1(char_idx, 67))
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
    var tm = time.time() - ts;
    println("Time used: %s sec".(tm));
    println("This machine benchmarks at %s SwarmStones/second".(LOOPS / tm));
}
