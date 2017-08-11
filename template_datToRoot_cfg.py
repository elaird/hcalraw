import FWCore.ParameterSet.Config as cms


process = cms.Process('source')
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))
process.source = cms.Source("NewEventStreamFileReader", fileNames=cms.untracked.vstring(FILEFLAG))
process.out = cms.OutputModule("PoolOutputModule", fileName=cms.untracked.string(OUTFLAG))
process.end = cms.EndPath(process.out)
process.schedule = cms.Schedule(process.end)

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.statistics = cms.untracked.vstring()
# process.MessageLogger.cerr.FwkReport.reportEvery = 10
