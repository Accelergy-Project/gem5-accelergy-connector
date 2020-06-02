#!/bin/csh

python3 orchestrator.py -m example/m5out -i example/input -o example/regress -c example/config.yaml
diff -rub example/output example/regress
if ($status == 0) then
    echo "OK"
else
    echo "FAIL"
endif
rm -r example/regress
