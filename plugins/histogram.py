import compare

def histogram(raw1={}, raw2={}, book=None, warnQuality=True, fewerHistos=False, **_):
    okFeds1 = compare.loop_over_feds(raw1, book, adcTag="feds1", warn=warnQuality, fewerHistos=fewerHistos)
    okFeds2 = compare.loop_over_feds(raw2, book, adcTag="feds2", warn=warnQuality, fewerHistos=fewerHistos)

