from ksdyn.core import KeystrokeCaptureData
from ksdyn.features import FeatureExtractor
from ksdyn.model import Fingerprint

def create_fingerprint_from_capture_data( name, capture_data ):
    assert isinstance( capture_data, KeystrokeCaptureData )
    fe= FeatureExtractor()
    capture_data.feed( fe )
    features= fe.extract_features()
    return Fingerprint.from_features( name, features ) 
