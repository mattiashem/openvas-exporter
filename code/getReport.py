from datetime import datetime
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
from gvm.xml import pretty_print
import xml.etree.ElementTree as ET
import untangle
import base64
import csv, json
import os
from os import path
from os import makedirs
import configparser
import sys
import getopt
import hashlib

'''
get the current datetime once
this won't be represent when the report was written to
disk but when we started the program. This is close enough
for our needs. Saves a minimal number of cycles but good practice
'''
current_datetime = datetime.now()

config = configparser.ConfigParser()
    
'''
This function reads in the list of already processed reports and stores it as an array
ranReports[reportID][filterID][date]
The date is just so people know when that report was first generated 
The data format of the incoming file is reportID, filterID, date
All values are in ASCII.
'''
def readRanReportsFile():
    ranReports = {}
    if os.path.isfile(config['DEFAULT']['reportfile']):
        try: 
            reportFile = open(config['DEFAULT']['reportfile'],'r')
        except IOError:
                print("Cannot open previously ran reports file. Please check file access or the config file")
    else:
        return ranReports
    reportData = reportFile.readlines();
    reportFile.close();
    i = 0
    for data in reportData:
        values = data.split(",", 2) #split at the comma, only return 1st 3 items
        # unnecessary use of variables here but it makes it easier to understand
        filterID = values[0].strip();
        reportID = values[1].strip();
        datetime = values[2].strip();
        key = filterID + reportID #this should be unique to every report and filter
        ranReports.update({key: datetime})
    return ranReports
#end readRanReportsFile
    
'''
This will add a target to the list and start the scan of the targets
First we get the report format ID associated with CSV output. Then
we grab a list of all reportIDs on the server. We then check to see if the
reportID is in the list of previous run reports for the chosen filter. If it is
then skip it. If not then grab the full report using that filter
'''
def exportReports(filterID, filterString, optPagination, optDetails, optRewrite):
    print('Loading previously completed reports data');
    ranReports = readRanReportsFile();

    #connect to our host as defined in the config file
    print ("Trying to connect to: '", config['DEFAULT']['host'], "' on port: '", config['DEFAULT']['port'],"'")
    connection = TLSConnection(hostname=config['DEFAULT']['host'],timeout=3600)
    if config['DEFAULT']['port']: 
        connection = TLSConnection(hostname=config['DEFAULT']['host'],port=config['DEFAULT']['port'],timeout=3600)
    print('Starting report processing')
    
    with Gmp(connection) as gmp:
        # Login
        print ("Attempting to authenticate")
        gmp.authenticate(config['DEFAULT']['username'], config['DEFAULT']['password'])
        print('Connected to:', config['DEFAULT']['host'])
        
        #Get the CSV report format ID. We use CSV as the base format to transform into json
        reportFormatID="" #holds the format id for CSV
        report_format = gmp.get_report_formats()
        report_root = ET.fromstring(report_format)
        for report in report_root:
            report.tag == "report_format"
            for report_format in report:
                if report_format.text == 'CSV result list.':
                    reportFormatID= report.attrib.get('id')

        getReports=[] #array of reportIDs
        print ('Getting reports')
        allreports = gmp.get_reports(details=0) #we only need the reportID so minimize the data returned
        print ('Retreived reports')
        allreports_root = ET.fromstring(allreports)
        print("Fetched the following scans from %s" %(config['DEFAULT']['host']))
        for report in allreports_root:
            if report.tag == 'report':
                for onereport in report:
                    if onereport.tag =='report':
                        pretty_print(onereport)
                        print(report.attrib)
                        getReports.append(report.attrib.get('id'))

        #Step through the reportID list and grab them as csv files
        for reportID in getReports:
            print("Processing Report ID: {0}".format(reportID))

            # we have a reportID. Check to see if it matches any existing reports already written to disk
            # if it does then we can skip this one. Note: we make sure filterID is null because we
            # only need to do the hashing once. 
            if filterString and not filterID:
                # we need a consistent identify for this string so hashes to the rescue
                # we are going to reuse the filterID variable to hold it
                sha_1 = hashlib.sha1() #instantiate hash
                sha_1.update(filterString.encode('utf-8')) #hash the string being sure to use proper encoding
                filterID = sha_1.hexdigest() #return the hash as a hex string                

            # we use the filterID and the reportID to create a key for the ranReports dict. If it exists then skip
            # that report unless we are over writing (or regenerating) reports. 
            ranReportsKey = filterID + reportID
            if ranReportsKey in ranReports and not optRewrite:
                print("This report was processed on %s" %(ranReports[ranReportsKey]))
                continue
                                            
            if filterString: #if they are using a custojer filter string entered on the CLI
                reportscv = gmp.get_report(reportID, filter=filterString, report_format_id=reportFormatID, ignore_pagination=optPagination, details=optDetails)
            else:
                reportscv = gmp.get_report(reportID, filter_id=filterID, report_format_id=reportFormatID, ignore_pagination=optPagination, details=optDetails)

            obj = untangle.parse(reportscv)
            resultID = obj.get_reports_response.report['id']
            base64CVSData = obj.get_reports_response.report.cdata
            data = str(base64.b64decode(base64CVSData),"utf-8")

            #Write the result to file
            writeResultToFile(resultID, data, filterID, filterString)
#end exportReports            

'''
This will write the CSV data into a file
'''    
def writeResultToFile(name, data, fpsuffix, filterString):
    if fpsuffix:
        reportPath = "{0}/{1}".format(config['DEFAULT']['datafolder'],fpsuffix)
        csvFilePath = "{0}/{1}.csv".format(reportPath, name)
        jsonFilePath = "{0}/{1}.json".format(reportPath,name)
        #create the directory if it doesn't exist
        if not path.isdir(reportPath):
            try: 
                os.makedirs(reportPath)
            except IOError:
                    print("Fatal eror: Could not create directories for reports on ", reportPath)
                    return 
        print("Created directory for filter ", fpsuffix)
        if filterString: #we want to save the filterString entered on the CLI 
            filterStringFile = "{0}/{1}/{2}".format(config['DEFAULT']['datafolder'],fpsuffix,'filter_string.txt')
            try: 
                fs = open(filterStringFile, "w")
                fs.write(filterString + '\n')
                fs.close()
            except IOError:
                    print("Non fatal error: Cannot write filter string to ", filterStringFile)
    else: 
        csvFilePath = "{0}/{1}.csv".format(config['DEFAULT']['datafolder'],name)
        jsonFilePath = "{0}/{1}.json".format(config['DEFAULT']['datafolder'],name)
    #end if fpsuffix
        
    print ('Writing CSV file: ', csvFilePath)
    try: 
        f = open(csvFilePath, "w")
        f.write(data)
        f.close()
    except IOError:
            print("Fatal error: Could not write CSV data to ", csvFilePath)
            return 
    #read the csv and add the data to a dictionary
    print ('Writing JSON file: ', jsonFilePath)
    try: 
        jsonFile = open(jsonFilePath, "w")
        with open (csvFilePath) as csvFile:
            csvReader = csv.DictReader(csvFile)
            for csvRow in csvReader:
                jsonFile.write(json.dumps(csvRow)+"\n")
    except IOError:
            print("Fatal error: Could not write JSON file to ", jsonFilePath)

    #write the reportID, filterID, and current date time to ranreports file
    # in the case of the overwrite optiosn being used we *do not* remove the
    # old entires from prior runs. We should but we don't. 
    try: 
        ranReportsFile = open(config['DEFAULT']['reportfile'],'a')
        ranReportsFile.write('%s, %s, %s\n' % (fpsuffix, name, current_datetime))
    except IOError:
            print("Non fatal error: Could not write previously raw reports data to ", config['DEFAULT']['reportfile'])

    ranReportsFile.close()
    jsonFile.close()
    csvFile.close()
#end writeResultToFile
    
def main(argv):
    filterID = ''
    filterString = ''
    pagination = True
    details = True
    rewriteReports = False
    configSuffix = 'ini'
    
    try:
        opts, args = getopt.getopt(argv, "hpdf:s:oi:")
    except getopt.GetoptError:
        print('getReport.py -f <filter id> [string]')
        print('             -i config file sufix [string]')
        print('             -d disable details')
        print('             -p enable pagination')
        print('             -s custom filter string [string]')
        print('             -o over write previously processed reports')
        pretty_print(getopt.GetoptError)
        sys.exit(2)
    #end except

    for opt, arg in opts:
        if opt == '-h':
            print('getReport.py -f <filter id>')
            print('             -i config file sufix [string]')            
            print('             -d disable details')
            print('             -p enable pagination')
            print('             -s custom filter string')
            print('             -o over write previously processed reports')
            sys.exit()
        elif opt == '-f':
            filterID = arg
        elif opt == '-p':
            pagination = False
        elif opt == '-d':
            details = False
        elif opt =='-s':
            filterString = arg;
        elif opt =='-o':
            rewriteReports = True
        elif opt == '-i':
            configSuffix = arg
        #end for

    configFile = './config/config.' + configSuffix
    config.sections()

    if os.path.isfile(configFile):
        try:
            config.read(configFile)
        except:
            print ('Cannot open config file at', configFile);
            sys.exit()
    else:
        print ('Config file does not exist at', configFile);
        sys.exit()
            
    if filterID and filterString:
        print ('-f and -s are mutually exclusive. Please use one or the other.')
        sys.exit()

    print ('Getting Ibex configuration from', configFile)
        
    if details:
        print('Details enabled')
    else:
        print('Details disabled')

    if pagination:
        print('Ignore pagination enabled')
    else:
        print('Ignore pagaination disabled')

    if filterID:
        print('Running reports with filter: ', filterID)
    else:
        print ('Running reports with no filter id')

    if filterString:
        print('Running custom report with filter: ', filterString)

    exportReports(filterID, filterString, pagination, details, rewriteReports)
#end main
    
if __name__ == "__main__":
    main(sys.argv[1:])
