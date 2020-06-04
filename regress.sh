#!/bin/csh

python3 orchestrator.py -m examples/minorcpu/m5out -i examples/minorcpu/input -o examples/minorcpu/regress -c examples/minorcpu/config.yaml
diff -rub examples/minorcpu/output examples/minorcpu/regress
if ($status == 0) then
    echo "OK"
else
    echo "FAIL"
endif
rm -r examples/minorcpu/regress
