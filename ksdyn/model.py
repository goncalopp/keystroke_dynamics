from ksdyn.core import VersionedSerializableClass, KeystrokeCaptureData
from features import FeatureExtractor, CompositeFeature, NormalFeature

import numpy as np

class Fingerprint(VersionedSerializableClass):
    FILE_EXTENSION=".fingerprint"
    CLASS_VERSION= 1
    def __init__(self, name, data ):
        assert isinstance(data, CompositeFeature)
        VersionedSerializableClass.__init__(self)
        self.name= name
        self.data= data
    
    def __repr__( self ):
        return "Fingerprint( {} )".format( self.name )

    @staticmethod
    def create_from_capture_data( name, capture_data ):
        assert isinstance( capture_data, KeystrokeCaptureData )
        fe= FeatureExtractor()
        capture_data.feed( fe )
        features= fe.extract_features()
        return Fingerprint( name, features )

class FingerprintComparer(object):
    def __init__(self, reducer=None):
        self._reducer= reducer if reducer is not None else self._multiplication_reducer
    
    @staticmethod
    def _multiplication_reducer( feature_similarities ):
        return reduce( lambda a,b: a*b, feature_similarities )

    @staticmethod
    def _mean_reducer( feature_similarities ):
        return np.mean( feature_similarities )
    
    def feature_similarity( self, f1, f2):
        print "computing similarity for features:    {}    {}".format(f1, f2)
        if type(f1)!=type(f1):
            raise Exception("Can't compare features of different types ({}, {})".format(type(f1),type(f2)))
        if f1.name!=f2.name:
            print "Warning: comparing features with different names ({}, {}))".format(f1.name, f2.name)
        if isinstance(f1, CompositeFeature):
            common_features= set(f1.keys()) & set(f2.keys()) #intersection of sets
            similarities= [self.feature_similarity( f1[k], f2[k] ) for k in common_features]
            return self._reducer( similarities )
        elif isinstance(f1, NormalFeature ):
            return f1.distribution.similarity( f2.distribution )
        else:
            raise Exception("Unknown feature type: {}".format(type(f1)))

    def fingerprint_similarity( self, f1, f2 ):
        print "computing similarity for fingerprints:    {}    {}".format(f1, f2)
        return self.feature_similarity( f1.data, f2.data ) 
