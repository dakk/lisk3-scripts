#!/bin/bash

if ! command -v jq &> /dev/null
then
    echo "jq not present"
    exit
fi
if ! command -v curl &> /dev/null
then
    echo "curl not present"
    exit
fi
if ! command -v lisk-core &> /dev/null
then
    echo "lisk-core not present or not in the PATH"
    exit
fi

apiToken="00000000:zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz" # your telegram api token
chat_id="00000000" # your telegram ID

while true; do
        data=$(lisk-core forging:status)

        address=`echo $data | jq -r '.[].address'`
        forging=`echo $data | jq -r '.[].forging'`
        height=`echo $data | jq -r '.[].height'`
        maxHeightPrevoted=`echo $data | jq -r '.[].maxHeightPrevoted'`
        maxHeightPreviouslyForged=`echo $data | jq -r '.[].maxHeightPreviouslyForged'`

        st="Your node is missing blocks! Lisk Forging: $forging - address: $address - height: $height - maxHeightPrevoted: $maxHeightPrevoted - maxHeightPreviouslyForged: $maxHeightPreviouslyForged"
        echo $st

        if [ $forging == 'false' ]; then
                curl -s -X POST https://api.telegram.org/bot$apiToken/sendMessage -d text="$(echo $st)" -d chat_id=$chat_id
        fi

        sleep 1800
done
