#!/usr/bin/python
import capture_keys
import pickle
from numpy import mean,std
from scipy.stats import norm
import Gnuplot, Gnuplot.funcutils
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
    def read_from_file( cls, filename):
        f=open(filename+self.FILE_EXTENSION, 'rb')
        data= pickle.load(f)
        f.close()

        load_error=None
        if not isinstance( data, cls ):
            load_error= 'Unexpected instance type'
        elif data._class_version!=self.CLASS_VERSION:
            load_error= 'Class version mismatch (expected "{}", got "{}")'.format( self.CLASS_VERSION, data._class_version)
        if load_error:
            raise TypeError("Failed to load serialized data from {}: {}".format(filename, load_error))

        return data

class TimingExtractor(KeypressEventReceiver):
    def __init__(self, timing_thresold=500):
        self.pt=0           #last press  time
        self.pk=0           #last pressed key
        self.press_time={}  #dictionary that associates currently depressed keys and
                            #their press times. Necessary because a key may be pressed
                            #before the preceding key is released
        
        self.timing_thresold= timing_thresold   # if timing betweeen events is bigger than this, ignore those events
        self.dwell_times=[[] for i in range(256)]
        self.flight_times_before=[[] for i in range(256)]
        self.flight_times_after=[[] for i in range(256)]
   

    def on_key(self, key, type, time):    
        if type==self.KEY_DOWN:
            flight_time= time - self.pt
            if flight_time<self.timing_thresold:
                self.flight_times_before[key].append(flight_time)
                self.flight_times_after[self.pk].append(flight_time)
            self.press_time[key]=time
            self.pt=time
            self.pk=key
            
        if type==self.KEY_UP:
            dwell_time= time - self.press_time.pop(key)
            if dwell_time<self.timing_thresold:
                self.dwell_times[key].append(dwell_time)

def fingerprint_extractor(keydata, sample_number_thresold=10, std_dev_thresold=20):
    fingerprint={}
    for i in range(len(keydata)):
        if (len(keydata[i])>=sample_number_thresold or sample_number_thresold==0) and (std(keydata[i])<=std_dev_thresold or std_dev_thresold==0):
            fingerprint[i]= (mean(keydata[i]), std(keydata[i]) ) 
    return fingerprint

def fingerprint_similarity(data, userfingerprint):
    datafingerprint= fingerprint_extractor(data, 1,0)
    score=1
    for key in userfingerprint:
        try:
            user_keyfingerprint=userfingerprint[key]
            data_keyfingerprint=datafingerprint[key]
            probability= key_similarity(user_keyfingerprint, data_keyfingerprint)
            score*= 2*probability
            
            print 'analising key %d, mean: %f, stddev: %f, given mean: %f, probability %f'% (key,user_keyfingerprint[0],user_keyfingerprint[1], data_keyfingerprint[0], probability)
        except:
            print 'no key %d on data fingerprint'%key
    return score

def key_similarity(userfingerprint, datafingerprint):
    stddev= userfingerprint[1]
    difference= abs(userfingerprint[0]-datafingerprint[0])
    return norm.cdf(-difference/stddev)
    

class KeystrokeCaptureData(KeypressEventReceiver, VersionedSerializableClass):
    '''Recorded data of actual keystrokes pressed by a user'''
    FILE_EXTENSION=".keypresses"
    CLASS_VERSION= 0
    
    def __init__(self):
        self.log= []

    def on_key(self, key, event_type, time_ms):
        '''Append a keypress event to this capture data'''
        self.log.append( (key, event_type, time_ms) )

def plot(datalists):
    colour=1
    gnuplotdatalist=[]
    for data in datalist:
        if type(data)==type([]):
            means=   [ mean(key) for key in data]
            stddevs= [ std(key) for key in data]
            plotdata= [[x+colour/5.0,means[x],stddevs[x]] for x in range(20,70)]
            
        if type(data)==type({}):
            plotdata= [[key+colour/5.0,data[key][0],data[key][1]] for key in data]
        
        gnuplotdata= Gnuplot.Data(plotdata, with_='yerrorbars '+str(colour)+' 1')
        colour+=1
        gnuplotdatalist.append(gnuplotdata)

    g = Gnuplot.Gnuplot()
    g.plot( *gnuplotdatalist)
    #g.hardcopy(filename+'.ps', enhanced=1, color=1)
    raw_input('Please press return to continue...\n')
    g.reset()



goncalo_fingerprint=load_fingerprint('goncalo')
yuna_fingerprint=load_fingerprint('yuna')


mytimingextractor=TimingExtractor(500)

def testf(*args):
    print args

#capture_keys.start(mytimingextractor.on_key)
capture_keys.start(testf)

#log= open_log(filename)
#for e in log:
#    mytimingextractor.on_key(e[0],e[1],e[2])

data=mytimingextractor.dwell_times


print "analysing data with goncalo fingerprint"
print fingerprint_similarity(data, goncalo_fingerprint)
print 
print "analysing data with yuna fingerprint"
print fingerprint_similarity(data, yuna_fingerprint)
print 
    
