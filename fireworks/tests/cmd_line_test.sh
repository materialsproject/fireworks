#!/bin/bash

lpad add fw_tutorials/firetask/fw_adder.yaml
for mode in "more" "less" "all"
do
    lpad get_wfs -d $mode
    lpad get_fws -d $mode
done
rlaunch singleshot
