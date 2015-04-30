#!/usr/bin/python
import pickle
import numpy
from scipy.stats import norm
from abc import ABCMeta, abstractmethod

class NormalDistribution(object):
    def __init__(self, mean=0.0, stddev=1.0):
        self.mean, self.stddev= mean, stddev

    @classmethod
    def estimate( cls, samples ):
        mean=   numpy.mean( samples )
        stddev= numpy.std(samples) #TODO: use proper Normal stddev estimation formula
        dist= cls( mean, stddev )
        return dist

    def similarity( self, other_normal ):
        '''quick-and-dirty hack. don't take this too seriously'''
        stddev= other_normal.stddev
        difference= abs(self.mean - other_normal.mean)
        return 2*norm.cdf(-difference/stddev)

    def __repr__(self):
        return "Normal({:.2f}, {:.2f})".format( self.mean, self.stddev )

class KeystrokeDynamicsFeature(object):
    '''A feature (in the machine learning sense) of a given typist'''
    __metaclass__=ABCMeta

    def __init__(self, name):
        self.name= str(name)

class CompositeFeature(KeystrokeDynamicsFeature, dict):
    '''A feature composed of multiple sub-features'''
    def __init__(self, name, subfeatures, reducer=None):
        '''reducer is a function. see reduce() documentation'''
        KeystrokeDynamicsFeature.__init__(self, name)
        if len(subfeatures)==0:
            raise Exception("Can't create a CompositeFeature with no subfeatures")
        for s in subfeatures:
            self[s.name]= s
    
    def __repr__(self):
        sep= "    "
        return "CompositeFeature( {} )".format( self.name )

class NormalFeature( KeystrokeDynamicsFeature ):
    '''A feature represented as a Normal distribution'''
    def __init__(self, name, samples):
        KeystrokeDynamicsFeature.__init__(self, name)
        self.nsamples= len(samples)
        if self.nsamples>1:
            self.distribution= NormalDistribution.estimate( samples )
        else:
            self.distribution= None
    
    def __repr__(self):
        return "NormalFeature({}, {})".format( self.nsamples, self.distribution )

class KeyDwellTime( NormalFeature ):
    '''A feature representing (the probability distribution of)
    the time while a certain key is pressed.
    The "name" attribute of this feature is the key name'''
    pass

class KeypressEventReceiver(object):
    '''A class that receives keypress events through a callback'''
    __metaclass__=ABCMeta
    KEY_DOWN, KEY_UP= 0, 1
    
    @abstractmethod
    def on_key(self, key, event_type, time_ms):
        '''key is a integer
        event_type is in (KEY_DOWN, KEY_UP)
        time_ms is the time when the key was (de/)pressed
        '''
        pass

class VersionedSerializableClass( object ):
    __metaclass__=ABCMeta
    FILE_EXTENSION=".pickle"
    CLASS_VERSION= -1

    def __init__(self, *args, **kwargs):
        self._class_version= self.CLASS_VERSION
    
    def save_to_file(self, filename):
        f= open(filename+self.FILE_EXTENSION, 'wb')
        pickle.dump( self, f)
        f.close()
    
    @classmethod
    def load_from_file( cls, filename):
        try:
            f= open(filename, 'rb')
        except Exception:
            f=open(filename+cls.FILE_EXTENSION, 'rb')
        instance= pickle.load(f)
        f.close()

        load_error=None
        if not isinstance( instance, cls ):
            load_error= 'Unexpected instance type'
        elif instance._class_version!=cls.CLASS_VERSION:
            load_error= 'Class version mismatch (expected "{}", got "{}")'.format( cls.CLASS_VERSION, instance._class_version)
        if load_error:
            raise TypeError("Failed to load serialized data from {}: {}".format(filename, load_error))

        return instance

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

        dwell_times= [KeyDwellTime(i, t) for i,t in enumerate(self.dwell_times) ]
        dwell_times= filter( feature_filter, dwell_times )

        return CompositeFeature( "dwell_times", dwell_times )

class KeystrokeCaptureData(KeypressEventReceiver, VersionedSerializableClass):
    '''Recorded data of actual keystrokes pressed by a user'''
    FILE_EXTENSION=".keypresses"
    CLASS_VERSION= 0

    def __init__(self):
        VersionedSerializableClass.__init__(self)
        self.log= []

    def on_key(self, key, event_type, time_ms):
        '''Append a keypress event to this capture data'''
        self.log.append( (key, event_type, time_ms) )

    def feed(self, event_receiver):
        '''feeds this data into a KeypressEventReceiver.
        Returns the event_receiver'''
        for event in self.log:
            event_receiver.on_key( *event )
        return event_receiver

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
        return numpy.mean( feature_similarities )
    
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
