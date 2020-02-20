#!/bin/sh

case $PREPARE_TYPE in
    time)
        python -m honeycomb_tools prepare-geoms-for-environment-for-time-range-for-source \
            --environment_name ${ENVIRONMENT_NAME:="capucine"} \
            --source $SOURCE \
            --start $START_TIME \
            --end $END_TIME
        break
        ;;
    inference)
        python -m honeycomb_tools prepare-geoms-for-inference-id-for-source \
            --inference_id $INFERENCE_ID \
            --source $SOURCE
        break
        ;;
    url)
        python -m honeycomb_tools prepare-geoms-for-environment-for-url-for-source \
            --environment_name ${ENVIRONMENT_NAME:="capucine"} \
            --source $SOURCE \
            --pickle_url $PICKLE_URL
        break
        ;;
    *)
        echo "Unknown prepare type: ${PREPARE_TYPE}"
        ;;
esac
