#!/bin/bash
#
#
# Script to startup openVas exporter and to loop it 
#

echo "Setup configfile"
envsubst </home/gvm/config/config.tmp> /home/gvm/config/config.ini

echo "Starting logstash"
/usr/share/logstash/bin/logstash -f /home/gvm/config/logstash.conf & 

echo "Starting the collector"
cd /home/gvm

echo "Looping"
while true
do
    python3 getReport.py
    echo "sleep"
    sleep 1m
done
