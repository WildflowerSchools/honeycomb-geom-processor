#!/bin/sh

python -m honeycomb_tools prepare-geoms-for-environment-for-time-range-for-source \
    --environment_name ${ENVIRONMENT_NAME:="capucine"} \
    --source $SOURCE \
    --start $START_TIME \
    --end $END_TIME