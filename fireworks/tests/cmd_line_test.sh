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
