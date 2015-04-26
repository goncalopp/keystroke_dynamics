#!/usr/bin/python
import pickle
from numpy import mean,std
from scipy.stats import norm
from abc import ABCMeta, abstractmethod

class KeypressEventReceiver(object):
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

class TimingExtractor(KeypressEventReceiver):
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


class KeystrokeCaptureData(KeypressEventReceiver, VersionedSerializableClass):
    '''Recorded data of actual keystrokes pressed by a user'''
    FILE_EXTENSION=".keypresses"
    CLASS_VERSION= 0
    
    def __init__(self):
        super(KeypressEventReceiver, self).__init__()
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
    CLASS_VERSION= 0
    def __init__(self, data):
        super(Fingerprint, self).__init__()
        self.data= data

    @staticmethod
    def create(keystroke_capture_data, sample_number_threshold=10, std_dev_threshold=20):
        snt, sdt= sample_number_threshold, std_dev_threshold
        times= keystroke_capture_data.feed(TimingExtractor(500)).dwell_times
        data={}
        for key,key_times in enumerate(times):
            if (len(key_times)>=snt or snt==0) and (std(key_times)<=sdt or sdt==0):
                data[key]= (mean(key_times), std(key_times) ) 
        return Fingerprint(data)
    
    def similarity( self, other_fingerprint ):
        def feature_similarity(f1, f2):
            stddev= f1[1]
            difference= abs(f1[0]-f2[0])
            return norm.cdf(-difference/stddev)
        fp1, fp2= self.data, other_fingerprint.data   #the two fingerprints
        score=1
        common_features= set(fp1.keys()) & set(fp2.keys()) #intersection of sets
        for feature in common_features:
            f1,f2= fp1[feature], fp2[feature]
            probability= feature_similarity( f1, f2 )
            score*= 2*probability
            print 'analising key %d, mean: %f, stddev: %f, given mean: %f, probability %f'% (feature,f1[0],f1[1], f2[0], probability)
        return score

