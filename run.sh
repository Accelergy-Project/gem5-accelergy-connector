#!/bin/csh

echo
echo "run minorcpu"
python3 connector.py -m examples/minorcpu/m5out -i examples/minorcpu/input \
-o examples/minorcpu/output -a examples/minorcpu/attributes.yaml -v

echo
echo "run o3cpu"
python3 connector.py -m examples/o3cpu/m5out -i examples/o3cpu/input \
-o examples/o3cpu/output -a examples/o3cpu/attributes.yaml -v
