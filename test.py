import capture_keys
from keystroke_dynamics import Fingerprint, TimingExtractor, KeystrokeCaptureData

goncalo_fingerprint=    Fingerprint.load_from_file('goncalo')
yuna_fingerprint=       Fingerprint.load_from_file('yuna')

#capture_keys.start(mytimingextractor.on_key)

data= KeystrokeCaptureData.load_from_file('goncalo')
data_fingerprint= Fingerprint.create( data )

print "analysing data with goncalo fingerprint"
print data_fingerprint.similarity( goncalo_fingerprint )
print 
print "analysing data with yuna fingerprint"
print data_fingerprint.similarity( yuna_fingerprint )
print 
    
