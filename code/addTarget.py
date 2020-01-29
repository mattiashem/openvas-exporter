from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
from gvm.xml import pretty_print
import xml.etree.ElementTree as ET


connection = TLSConnection(hostname="gvmd")



def addTargetToSca(target,scantype,scanscanner):
    '''
     This will add a target to the list and start the sca of the targets
    '''


    with Gmp(connection) as gmp:
        # Login
        gmp.authenticate('admin', 'admin')
        theTargetName=str("target_{0}".format(target.replace('.','-')))
        

        #Create target
        gmp.create_target(theTargetName, hosts=[target], comment="Auto generated")


        #Get the targets ID
        targetID=""
        targets = gmp.get_targets(filter=theTargetName)
        #pretty_print(targets)
        root = ET.fromstring(targets)
        for target in root:
            if target.tag == 'target':
                targetID = target.attrib.get('id')



        #GEt the configs to use
        configID=""
        configs = gmp.get_configs(filter=scantype)
        #pretty_print(configs)
        rootConfig = ET.fromstring(configs)
        for configs in rootConfig:
            if configs.tag == 'config':

                for config in configs:
                    if config.text == scantype:
                        configID = configs.attrib.get('id')


        #Get the scanner id
        scannerID=""
        scanners = gmp.get_scanners(filter=scanscanner)
        #pretty_print(configs)
        rootScanner = ET.fromstring(scanners)
        for scanner in rootScanner:
            if scanner.tag == 'scanner':
                for scan in scanner:
                    if scan.text == scanscanner:
                        scannerID =scanner.attrib.get('id')

        back = gmp.create_task(theTargetName,config_id=configID,target_id=targetID,scanner_id=scannerID)   
        taskResponse = ET.fromstring(back)
        task_id = taskResponse.attrib.get('id')


        #Start the task
        gmp.start_task(task_id)

addTargetToSca('10.100.0.103','Full and fast','OpenVAS Default')