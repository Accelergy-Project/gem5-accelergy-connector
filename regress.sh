#!/bin/csh

echo "minorcpu"
python3 connector.py -m examples/minorcpu/m5out -i examples/minorcpu/input -o examples/minorcpu/output -c examples/minorcpu/config.yaml -d

echo "o3cpu"
python3 connector.py -m examples/o3cpu/m5out -i examples/o3cpu/input -o examples/o3cpu/output -c examples/o3cpu/config.yaml -d

# diff -rub examples/minorcpu/output examples/minorcpu/regress
# if ($status == 0) then
#     echo "OK"
# else
#     echo "FAIL"
# endif
# rm -r examples/minorcpu/regress
