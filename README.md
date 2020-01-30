# OpenVas report exporter
Will export the openvas reports and store them into JSON files with newline per finding.
The JSON files can then bed read by Logstash and sent to ElasticSearch ore simular


- Only export every report once
- Connect over TLS to gsad 
- Can also add new target and create scan for them



## Make shoure gvmd is lissen on port 9390
The script connect to gvmd on port 9390 to lissen for connections.
So before it to work verify that your gvmd is lissen on that port.

If you install openvas on ubuntu you need to enable gvmd to lissen for the ports by


Edit /etc/defualt/gvmd and uncommet LISSEN adn PORT values


```
vi /etc/defualts/gvmd
```


Restart gvmd

```
systemctl stop gvmd
systemctl start gvmd
```

(systemctl restart did not work when i tested ....)


Verify with 

```
telnet 127.0.0.1 9390
```

## How to run as docker

Easy way is to run the exporter as docker image. 

```
docker run -it sammascanner/openvas-exporter

```


The values to set are 

- USERNAME = gsad username
- PASSWORD = gsad password
- GSAD_HOST = Hostname / ip to gvmd



## Run as python script on local server

### Install deps

- Python 3
- pip3 install gvm-tools untangle python-gvm


### Clonde this repo

Clone this repo into the opt folder (You can use other if you want but check config)


```
cd /opt
git clone git@github.com:mattiashem/openvas-exporter.git
```

### Alter your config.ini file
Setup and chnage your config.ini file to have the values for your gsad

```
[DEFAULT]
username=admin
password=admin
host=gvmd
datafolder=data
```

### Setup the datafolder 

setup the data folder if not excists.


```
If needed
mkdir /opt/openvas-exporter/code/data
```

### Create a user for the script to run from 

** Not NEED **

Then script CAN NOT BE RUN AS ROOT
Create a user account to be used.


```
adduser gvm
```

Fix the permissions


```

chown gvm:gvm -R /opt/openvas-exporter/
```

### Start the sync

Now you can run the sync 


```
python3 getReport.py
```

Look in logs for error


The script will crate .csv and .json files in the data folder. Look ther for the outcome and verify that contet are written.


Keep track

To keep track of what reports have eban generated the script look for a file with the ID of the report and extension .json.
If that file excciste then the report is not process.

If you want to get all reports again you can delete all the files in the foldr to generate new json files.
Ore you can delete the file with th id of the report you want to regenerate.3


## Logstash
TO use logstash to send the event you can use the configfile in the config folder.
Change the 

```
 file {
    path => "/home/gvm/data/*.json"
```

to 

```
 file {
    path => "/opt/openvas-exporter/code/data/*.json"
```
When using the python script only


To send the logs to some other host like elastic add a new output

```
output {
    if "openvas" in [tags] {
 
    stdout {
    }
    }
  
}
```

to 

```
output {

if "openvas" in [tags] {
    stdout {
    }
    elasticsearch {
      hosts => ["$ELASTICSEARCH"]
      index => "logstash-openvas-%{+YYYY.MM}"
    }
}
}
```


## Trobbelshout

To test the script erase all the files in the data folder.
Then run the script.

Now yous should see some json files in the data folder.

- If no json files = the script cannot connect to gvmd. Check the port are open and you have correct user and password


- If json file go to logstash and check it reads the log. the patch to the data folder is correct and the output is correct.

### Test logstash 
you cna test the logstash config by running it local.
Open the file logstash_test.conf anf verify the 

```
    path => "/home/gvm/data/*.json"

```
ispoting to the correct data folder

```
logstash -f logstash_test.conf
```

This shoul print the alerts into your terminal.


### Reset

To reset all results simple delete alla the files in the data folder.
