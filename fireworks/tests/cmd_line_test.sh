#!/bin/bash

function test_cmd {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "error with $1"
        exit -1
    fi
    return $status
}

test_cmd lpad reset --password `date "+%Y-%m-%d"`
test_cmd lpad add fw_tutorials/firetask/fw_adder.yaml
for mode in "more" "less" "all"
do
    test_cmd lpad get_wflows -d $mode
    test_cmd lpad get_fws -d $mode
done
rlaunch singleshot

test_cmd lpad append_wflow -i 1 -f fw_tutorials/firetask/fw_adder.yaml
test_cmd lpad dump_wflow -i 1 -f test_dump_wflow.json && rm -f test_dump_wflow.json
test_cmd rlaunch singleshot
test_cmd lpad delete_wflows -i 1
