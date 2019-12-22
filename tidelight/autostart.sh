#!/bin/bash
SCRIPT=`realpath $0`
echo $SCRIPT
len=`expr length $SCRIPT`
echo $len
indexes=$(($len - 13))
echo $indexes
path=${SCRIPT:0:indexes }
insertedcommand="sudo -- bash -c \"cd $path && nohup python3 -u main.py &\""
echo $path
echo $insertedcommand
grepresult="$(grep -nr 'exit 0' /etc/rc.local | tail -1 | cut -d : -f 1)"
echo $grepresult
i="i"
sedargument="$grepresult$i $insertedcommand"
echo $sedargument
sed -i "$sedargument"  /etc/rc.local
