from ksdyn.core import KeypressEventReceiver, Named, DictTree

import numpy as np
from abc import ABCMeta, abstractmethod
from collections import defaultdict


class Feature(Named):
    '''A feature (in the machine learning sense) from a given typist'''
    __metaclass__=ABCMeta

class CompositeFeature(DictTree, Feature):
    '''A feature composed of multiple sub-features'''
    pass

class RealNumberSeq(Feature):
    '''A sequence of real numbers'''
    def __init__(self, name, data):
        Feature.__init__(self, name)
        self.data= data

class KeyDwellTimes( RealNumberSeq ):
    '''A sequence of times time while a certain keyboard key is pressed.
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
        self.dwell_times=           defaultdict(list)
        self.flight_times_before=   defaultdict(list)
        self.flight_times_after=    defaultdict(list)

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
    
    def extract_features( self ):
        '''Extracts the features from the processed data.
        Returns a CompositeFeature, composed of multiple other CompositeFeatures.'''
        dwell_times= [KeyDwellTimes(k, v) for k,v in self.dwell_times.items()]

        return CompositeFeature( "dwell_times", dwell_times ) 
