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

test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml reset --password `date "+%Y-%m-%d"`
test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml add fw_tutorials/firetask/fw_adder.yaml
for mode in "more" "less" "all"
do
    test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml get_wflows -d $mode
    test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml get_fws -d $mode
done
test_cmd rlaunch -l fireworks/tests/my_launchpad_unittest.yaml singleshot

test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml append_wflow -i 1 -f fw_tutorials/firetask/fw_adder.yaml
test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml dump_wflow -i 1 -f test_dump_wflow.json && rm -f test_dump_wflow.json
test_cmd rlaunch -l fireworks/tests/my_launchpad_unittest.yaml singleshot
test_cmd lpad -l fireworks/tests/my_launchpad_unittest.yaml delete_wflows -i 1
