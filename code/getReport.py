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

# Read the configfile
config = configparser.ConfigParser()
config.sections()
config.read('config/config.ini')


def exportReports(filterID, filterString, optPagination, optDetails):
    '''
     This will add a target to the list and start the scan of the targets
    '''

    connection = TLSConnection(hostname=config['DEFAULT']['host'],timeout=300)
    print('Starting report processing')
    
    with Gmp(connection) as gmp:
        # Login
        gmp.authenticate(config['DEFAULT']['username'], config['DEFAULT']['password'])
        print('Connected to:', config['DEFAULT']['host'])
        
        #Get the CSV report type
        reportFormatID=""
        report_format = gmp.get_report_formats()
        report_root = ET.fromstring(report_format)
        for report in report_root:
            report.tag == "report_format"
            for report_format in report:
                if report_format.text == 'CSV result list.':
                    reportFormatID= report.attrib.get('id')

        getReports=[]
        print ('Getting reports')
        allreports = gmp.get_reports()
        allreports_root = ET.fromstring(allreports)
        for report in allreports_root:
            if report.tag == 'report':
                for onereport in report:
                    if onereport.tag =='report':
                        pretty_print(onereport)
                        print(report.attrib)
                        getReports.append(report.attrib.get('id'))


        #Get out the reports and get them as csv files to use
        for reportID in getReports:
            print("Report ID: {0}".format(reportID))

            if filterString:
                reportscv = gmp.get_report(reportID, filter=filterString, report_format_id=reportFormatID, ignore_pagination=optPagination, details=optDetails)
                # we need a consistent identify for this string so hashes to the rescue
                # we are going to reuse the filterID variable to hold it
                sha_1 = hashlib.sha1() #instantiate hash
                sha_1.update(filterString.encode('utf-8')) #hash the string being sure to use proper encoding
                filterID = sha_1.hexdigest() #return the hash as a hex string
            else:
                reportscv = gmp.get_report(reportID, filter_id=filterID, report_format_id=reportFormatID, ignore_pagination=optPagination, details=optDetails)

            obj = untangle.parse(reportscv)
            resultID = obj.get_reports_response.report['id']
            base64CVSData = obj.get_reports_response.report.cdata
            data = str(base64.b64decode(base64CVSData),"utf-8")

            #Write the result to file
            writeResultToFile(resultID,data,filterID, filterString)
#end exportReports            

def writeResultToFile(name,data,fpsuffix, filterString):
    '''
    This will write the data into a file
    '''
    
    if fpsuffix:
        reportPath = "{0}/{1}".format(config['DEFAULT']['datafolder'],fpsuffix)
        csvFilePath = "{0}/{1}.csv".format(reportPath, name)
        jsonFilePath = "{0}/{1}.json".format(reportPath,name)
        #create the directory if it doesn't exist
        if not path.isdir(reportPath):
            os.makedirs(reportPath)
            print("Created directory for filter ", fpsuffix)
        if filterString:
            filterStringFile = "{0}/{1}/{2}".format(config['DEFAULT']['datafolder'],fpsuffix,'filter_string.txt')
            fs = open(filterStringFile, "w")
            fs.write(filterString + '\n')
            fs.close()
    else:
        csvFilePath = "{0}/{1}.csv".format(config['DEFAULT']['datafolder'],name)
        jsonFilePath = "{0}/{1}.json".format(config['DEFAULT']['datafolder'],name)
        
    if (hasThisBeenDone(name,jsonFilePath) == False):
        return
    
    print ('Writing CVS file: ', csvFilePath)
    f = open(csvFilePath, "w")
    f.write(data)
    f.close()
    
    #read the csv and add the data to a dictionary
    print ('Writing JSON file: ', jsonFilePath)
    jsonFile = open(jsonFilePath, "w")

    with open (csvFilePath) as csvFile:
        csvReader = csv.DictReader(csvFile)
        for csvRow in csvReader:
            jsonFile.write(json.dumps(csvRow)+"\n")
    #end with

    jsonFile.close()
    csvFile.close()
#end writeResultToFile
    
def hasThisBeenDone(id, dataPath):
    '''
    Check if a report has already been proccessed
    '''
    if path.exists(dataPath):
        print('We have already processed this report')
        return False
    else:
        return True
#end hasThisBeenDone
    
def main(argv):
    filterID = ''
    filterString = ''
    pagination = True
    details = True

    try:
        opts, args = getopt.getopt(argv, "hpdf:s:")
    except getopt.GetoptError:
        print('getReport.py -f <filter id>')
        print('             -d disable details')
        print('             -p enable pagination')
        print('             -s custom filter string')
        pretty_print(getopt.GetoptError)
        sys.exit(2)
    #end excpet

    for opt, arg in opts:
        if opt == '-h':
            print('getReport.py -f <filter id>')
            print('             -d disable details')
            print('             -p enable pagination')
            print('             -s custom filter string')
            sys.exit()
        elif opt == '-f':
            filterID = arg
        elif opt == '-p':
            pagination = False
        elif opt == '-d':
            details = False
        elif opt =='-s':
            filterString = arg;
    #end for

    if filterID and filterString:
        print ('-f and -s are mutually exclusive. Please use one or the other.')
        sys.exit();

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

    exportReports(filterID, filterString, pagination, details)
#end main
    
if __name__ == "__main__":
    main(sys.argv[1:])
