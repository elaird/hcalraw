import FWCore.ParameterSet.Config as cms

process = cms.Process("demo")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32(25)

process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.GlobalTag.globaltag = "GR_P_V40_AN1::All"

utca = False
produceDigis = False

kargs = {"UnpackZDC": cms.untracked.bool(False),
         "UnpackTTP": cms.untracked.bool(False),
         "FilterDataQuality": cms.bool(False),
         "InputLabel": cms.InputTag("source" if utca else "foo"),
         "ComplainEmptyData": cms.untracked.bool(True),
         "UnpackCalib": cms.untracked.bool(True),
         "lastSample": cms.int32(9),
         "firstSample": cms.int32(0),
         }
if utca :
    kargs["FEDs"] = cms.untracked.vint32(989)
    kargs["silent"] = cms.untracked.bool(False)

process.hcalDigis = cms.EDProducer("HcalRawToDigi", **kargs)

if utca :
    process.source = cms.Source("HcalTBSource",
                                maxEvents = cms.untracked.int32(-1),
                                streams = cms.untracked.vstring('HCAL_Trigger', 'HCAL_DCC989'),
                                fileNames = cms.untracked.vstring('file:/afs/cern.ch/user/c/chhill/public/parasiticData/uTCArootFiles/parasitic_CMSrun3453_usc209150_dec16-2012.root')

                                #streams = cms.untracked.vstring('HCAL_Trigger', 'HCAL_DCC700'),
                                #fileNames = cms.untracked.vstring('file:/afs/cern.ch/user/e/elaird/USC_209311.root')
                                )
    #process.load("CalibCalorimetry.HcalPlugins.Hcal_FakeConditions_cff")
    #process.load("CalibCalorimetry.HcalPlugins.Hcal_FrontierConditions_cff")

    process.p = cms.Path(process.hcalDigis) if produceDigis else cms.Path()
else :
    process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(-1))
    process.source = cms.Source("PoolSource",
                                fileNames = cms.untracked.vstring(
        "file:/afs/cern.ch/user/e/elaird/12_utca/209151.7AB1CF02-D647-E211-B6E0-003048D3751E.root")
                                )

    process.hlt = cms.EDFilter("HLTHighLevel",
                               TriggerResultsTag = cms.InputTag("TriggerResults","","HLT"),
                               HLTPaths = cms.vstring("HLT_HcalUTCA_v1"), # list of HLT paths (or patterns)
                               eventSetupPathsKey = cms.string(''),
                               andOr = cms.bool(True), # for multiple triggers: True does OR; False does AND
                               throw = cms.bool(True), # throw exception on unknown path names
                               )

    process.p = cms.Path(process.hlt * process.hcalDigis) if produceDigis else cms.Path(process.hlt)

process.out = cms.OutputModule("PoolOutputModule",
                               outputCommands = cms.untracked.vstring('drop *','keep *'),
                               fileName = cms.untracked.string('%s.root'%("utca" if utca else "cms")),
                               SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('p')),
                               )
process.e = cms.EndPath(process.out)
