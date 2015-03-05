#!/usr/bin/env python

import subprocess,collections

def commandOutput(cmd = "") :
    return subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).communicate()[0].split()

def collectedStatus(baseDir = "", minRun = 0, quiet = False, addZeros = False, requestStage = False, copy = False) :
    print baseDir
    out = collections.defaultdict(list)
    for subDir in commandOutput("nsls %s"%baseDir) :
        if int(subDir)<minRun : continue
    
        fullDir = "/".join([baseDir, subDir, "00000" if addZeros else ""])
        fileNames = commandOutput("nsls %s"%fullDir)
        
        fileOne = "%s/%s"%(fullDir, fileNames[0])
        try:
            status = commandOutput("stager_qry -M %s"%fileOne)
            statusCode = status[-1]
            if not quiet : print subDir,statusCode
            if statusCode=="class)" :
                out["NOT STAGED"].append(subDir)
                if requestStage :
                    print "stager_get -M %s"%fileOne
                    commandOutput("stager_get -M %s"%fileOne)
            elif statusCode=="STAGEIN":
                out[statusCode].append(subDir)
            elif statusCode=="STAGED" :
                out[statusCode].append(fileOne)
                print fileOne
                
        except:
            pass
    return out

def printDict(d = {}) :
    for key,value in d.iteritems() :
        print key,value

#statusD = collectedStatus(baseDir = "/castor/cern.ch/cms/store/hidata/HIRun2013/L1Accept/RAW/v1/000/210",
#                          addZeros = True,
#                          minRun = 530,
#                          )
#printDict(statusD)

#status = collectedStatus(baseDir = "/castor/cern.ch/cms/store/hidata/HIRun2013/HcalNZS/RAW/v1/000/210/",
#                         addZeros = True,
#                         requestStage = False,
#                         )
#printDict(status)
#
statusA = collectedStatus(baseDir = "/castor/cern.ch/cms/store/hidata/HIRun2013A/HcalNZS/RAW/v1/000/210/",
                          addZeros = False,
                          requestStage = False,
                          minRun = 348,
                          copy = False,
                          )
printDict(statusA)
