from ksdyn.core import KeypressEventReceiver

import numpy as np
from scipy.stats import norm
from abc import ABCMeta, abstractmethod

class InsufficientData(Exception):
    pass

class NormalDistribution(object):
    def __init__(self, mean=0.0, stddev=1.0, nsamples=None):
        self.mean, self.stddev= mean, stddev
        self.nsamples= nsamples

    @staticmethod
    def estimate_parameters( samples ):
        nsamples= len(samples)
        if nsamples<2:
            raise InsufficientData()
        mean=   np.mean( samples )
        stddev= np.std(samples) #TODO: use proper Normal stddev estimation formula
        return mean, stddev, nsamples

    def similarity( self, other_normal ):
        '''quick-and-dirty hack. don't take this too seriously'''
        stddev= other_normal.stddev
        difference= abs(self.mean - other_normal.mean)
        return 2*norm.cdf(-difference/stddev)

    def __repr__(self):
        return "{}({:.2f}, {:.2f}, {})".format( self.__class__.__name__, self.mean, self.stddev, self.nsamples )

class KeystrokeDynamicsFeature(object):
    '''A feature (in the mach ine learning sense) from a given typist'''
    __metaclass__=ABCMeta

    def __init__(self, name):
        self.name= str(name)

class CompositeFeature(KeystrokeDynamicsFeature, dict):
    '''A feature composed of multiple sub-features'''
    def __init__(self, name, subfeatures):
        '''reducer is a function. see reduce() documentation'''
        KeystrokeDynamicsFeature.__init__(self, name)
        if len(subfeatures)==0:
            raise Exception("Can't create a CompositeFeature with no subfeatures")
        for s in subfeatures:
            self[s.name]= s
    
    @staticmethod
    def getCommonFeatures( *features ):
        '''Given N CompositeFeature, returns N CompositeFeature, such that
        each outputed CompositeFeature has the same feature values of each 
        input, but only for subfeatures common for all inputs'''
        recursive= True
        common_names= reduce(set.intersection, [set(f.keys()) for f in features])
        def get_subfeatures( subfeature_name ):
            subfeatures= [f[subfeature_name] for f in features]
            is_composite= subfeatures and isinstance(subfeatures[0], CompositeFeature)
            if recursive and is_composite:
                subfeatures= CompositeFeature.getCommonFeatures(*subfeatures)
            return subfeatures
        all_subfeatures= zip(*map( get_subfeatures, common_names ))
        return [CompositeFeature(f.name, subs) for f,subs in zip(features, all_subfeatures)]


class NormalFeature( KeystrokeDynamicsFeature, NormalDistribution ):
    '''A feature represented as a Normal distribution'''
    def __init__(self, name, samples):
        KeystrokeDynamicsFeature.__init__(self, name)
        NormalDistribution.__init__( self, *NormalDistribution.estimate_parameters( samples ) )

class KeyDwellTimeDistribution( NormalFeature ):
    '''A feature representing (the probability distribution of)
    the time while a certain key is pressed.
    The "name" attribute of this feature is the key name'''
    pass
 
class FeatureExtractor(KeypressEventReceiver):
    '''Extracts features from keypress data'''
    def __init__(self, timing_threshold=500):
        self.pt=0           #last press  time
        self.pk=0           #last pressed key
        self.press_time={}  #dictionary that associates currently depressed keys and
                            #their press times. Necessary because a key may be pressed
                            #before the preceding key is released
        
        self.timing_threshold= timing_threshold   # if timing betweeen events is bigger than this, ignore those events
        self.dwell_times=[[] for i in range(256)]
        self.flight_times_before=[[] for i in range(256)]
        self.flight_times_after=[[] for i in range(256)]
   

    def on_key(self, key, type, time):
        if type==self.KEY_DOWN:
            flight_time= time - self.pt
            if flight_time<self.timing_threshold:
                self.flight_times_before[key].append(flight_time)
                self.flight_times_after[self.pk].append(flight_time)
            self.press_time[key]=time
            self.pt=time
            self.pk=key
        
        if type==self.KEY_UP:
            try:
                dwell_time= time - self.press_time.pop(key)
            except KeyError:
                #can happen because we initiated capture with a key pressed down
                return
            if dwell_time<self.timing_threshold:
                self.dwell_times[key].append(dwell_time)
    
    def extract_features( self, sample_number_threshold=5):
        '''Extracts the features from the processed data.
        Returns a CompositeFeature, composed of multiple other CompositeFeatures.
        Doesn't set any CompositeFeature.reducer.'''
        snt = sample_number_threshold
        feature_filter= lambda f: f.nsamples>=snt 

        dwell_times= [KeyDwellTimeDistribution(i, t) for i,t in enumerate(self.dwell_times) if len(t)>1 ]
        dwell_times= filter( feature_filter, dwell_times )

        return CompositeFeature( "dwell_times", dwell_times ) 
