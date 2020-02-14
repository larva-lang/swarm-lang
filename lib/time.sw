!<<

import (
    "time"
)

!>>

public func time()
{
    !<<
    return sw_obj_float_from_go_float(float64(time.Now().UnixNano()) / 1e9)
    !>>
}
