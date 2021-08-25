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
    data=$(lisk-core node:info)

	height=`echo $data | jq -r '.height'`
	finheight=`echo $data | jq -r '.finalizedHeight'`
    timetochange=$(((16332092 - $height) * 10 / 60 / 60))
    ttchdays=$((timetochange / 24))
    ttchhours=$((timetochange % 24))

    st="Lisk Stats - height: $height - finheight: $finheight - timetochange: $ttchdays days and $ttchhours hours" 
    echo $st
    curl -s -X POST https://api.telegram.org/bot$apiToken/sendMessage -d text="$(echo $st)" -d chat_id=$chat_id
	
	sleep 3600
done
