#!/bin/sh

python -m honeycomb_tools prepare-geoms-for-environment-for-time-range \
    --environment_name ${ENVIRONMENT_NAME:="capucine"} \
    --source cuwb \
    --start $START_TIME \
    --end $END_TIME
