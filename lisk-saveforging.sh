#!/bin/bash
# Developed by corsaro and dakk

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

olda=$(lisk-core forging:status)

while true; do
	a=$(lisk-core forging:status)
	aheightforged=`echo $a | jq -r '.[].maxHeightPreviouslyForged'`
	oldaaheightforged=`echo $olda | jq -r '.[].maxHeightPreviouslyForged'`

	echo "Previously forged: $aheightforged; New value: $oldaaheightforged"

	if [[ "$aheightforged" -gt "$oldaaheightforged" ]]
	then
	    address=$(echo $a | jq -r '.[].address')
	    height=$(echo $a | jq -r '.[].height')
	    maxHeightPreviouslyForged=$aheightforged
	    maxHeightPrevoted=$(echo $a | jq -r '.[].maxHeightPrevoted')
	    # $address $height $maxHeightPreviouslyForged $maxHeightPrevoted
	    echo "Forged Block $address - $height - $maxHeightPreviouslyForged" 
	    curl -s -X POST https://api.telegram.org/bot$apiToken/sendMessage -d text="Lisk forged block - address:'$address' height:'$height' maxHeightPreviouslyForged:'$maxHeightPreviouslyForged' maxHeightPrevoted: '$maxHeightPrevoted'" -d chat_id=$chat_id
	fi
	
	olda=$a
	
	sleep 30
done
