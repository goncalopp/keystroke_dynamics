from ksdyn.core import VersionedSerializableClass, GaussianDistribution, KeystrokeCaptureData, Named, DictTree, InsufficientData
from features import FeatureExtractor, CompositeFeature, FloatSeq

import numpy as np
from abc import ABCMeta, abstractmethod

class Model(Named):
    '''A model (in the machine learning sense).'''
    __metaclass__=ABCMeta

    @abstractmethod
    def fit( self, data, labels=None ):
        '''makes the model fit some data (i.e.: trains the model)'''
        pass

    @abstractmethod
    def predict(self, data):
        '''given some data, outputs model predictions'''
        pass
    
    @classmethod
    def from_features(cls, name, data):
        m= cls(name)
        m.fit(data)
        return m
    
    def __repr__( self ):
        return "{}( {} )".format( self.__class__.__name__, self.name )


class CompositeModel(DictTree, Model):
    '''A model composed of multiple sub-models'''
    pass

class GaussianAnomalyModel( Model, GaussianDistribution ):
    '''A anomaly detection model using a Gaussian distribution'''
    def fit( self, data, labels=None ):
        '''data must be a iterable of numbers. '''
        if labels is not None:
            raise NotImplementedError( "Don't provide labels - all data should represent non-anomalies")
        parameters= GaussianDistribution.estimate_parameters( data )
        GaussianDistribution.__init__( self, *parameters )

    def predict(self, data):
        '''data must be a iterable of numbers'''
        return map(self.similarity_number, data )

class KeyDwellTime( GaussianAnomalyModel ):
    '''A model representing (the probability distribution of)
    the time while a certain keyboard key is pressed.
    The "name" attribute of this feature is the key name'''
    pass

class Fingerprint(CompositeModel, VersionedSerializableClass):
    '''A model that models many different aspects of a given typist,
    thus being able to uniquely identify them'''
    FILE_EXTENSION=".fingerprint"
    CLASS_VERSION= 1
    def __init__(self, name):
        '''Name argument is the typist's name'''
        VersionedSerializableClass.__init__(self)
        CompositeModel.__init__(self, name)

    def fit( self, data, labels=None ):
        def feature_map(*features):
            assert len(features)==1
            f= features[0]
            try:
                if isinstance( f, FloatSeq ):
                    return GaussianAnomalyModel.from_features( f.name, f.data )
                else:
                    raise Exception("Unknown feature: {}".format(f))
            except InsufficientData:
                return self.IGNORE_CHILD
        assert isinstance( data, CompositeFeature)
        newmodel= DictTree.map( feature_map, data)
        self.clear()
        self.update( newmodel )

class FingerprintComparer(object):
    def __init__(self, reducer=None):
        self._reducer= reducer or self._multiplication_reducer

    @staticmethod
    def _multiplication_reducer( feature_similarities ):
        return feature_similarities.reduce( lambda a,b: a*b )

    @staticmethod
    def _mean_reducer( feature_similarities ):
        score_tree= feature_similarities.map( lambda x: (1,x.score) )
        summed= score_tree.reduce( lambda (na,sa),(nb,sb): (na+nb), (sa+sb))
        return summed[1]/summed[0]

    def _fingerprint_similarity( self, f1, f2 ):
        print "computing similarity for fingerprints:    {}    {}".format(f1, f2)
        f1,f2= DictTree.intersect( f1, f2 )
        def feature_map(*features):
            f1,f2= features
            return f1.similarity(f2)
        similarities= DictTree.map( feature_map, f1, f2 )
        return self._reducer( similarities )   

    def similarity(self, f1, x):
        assert isinstance(f1, Fingerprint)
        if isinstance(x, Fingerprint):
            return self._fingerprint_similarity( f1, x )
        else: #assume x is a feature
            raise NotImplementedError

class FingerprintDatabase(object):
    def __init__(self, fingerprints=[], comparer=None):
        comparer= comparer or FingerprintComparer()
        self.fingerprints= fingerprints
        self.comparer= comparer

    def score( self, data ):
        return [self.comparer.similarity( f, data ) for f in self.fingerprints]

    def best_match( self, data ):
        if len(self.fingerprints)==0:
            raise Exception("No fingerprints available for matching")
        scores= self.score(data)
        for f,score in zip(self.fingerprints, scores):
            print "Score for {}: {}".format(f.name, score)
        best_i= scores.index(max(scores))
        best= self.fingerprints[best_i]
        return best

    def load_from_dir( self, directory ):
        import os
        d= directory
        files= [os.path.join(d,f) for f in os.listdir(d) if f.endswith(Fingerprint.FILE_EXTENSION)]
        fingerprints= map( Fingerprint.load_from_file, files)
        self.fingerprints.extend( fingerprints )
        return self
