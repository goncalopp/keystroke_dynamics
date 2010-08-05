#!/usr/bin/python
import capture_keys
import pickle
from numpy import mean,std
from scipy.stats import norm
import Gnuplot, Gnuplot.funcutils

class TimingExtractor():
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
   

    def keypress(self, key, type, time):    
        if type==0:
            flight_time= time - self.pt
            if flight_time<self.timing_thresold:
                self.flight_times_before[key].append(flight_time)
                self.flight_times_after[self.pk].append(flight_time)
            self.press_time[key]=time
            self.pt=time
            self.pk=key
            
        if type==1:
            dwell_time= time - self.press_time.pop(key)
            if dwell_time<self.timing_thresold:
                self.dwell_times[key].append(dwell_time)
                
def signature_extractor(keydata, sample_number_thresold=10, std_dev_thresold=20):
    signature={}
    for i in range(len(keydata)):
        if (len(keydata[i])>=sample_number_thresold or sample_number_thresold==0) and (std(keydata[i])<=std_dev_thresold or std_dev_thresold==0):
            signature[i]= (mean(keydata[i]), std(keydata[i]) ) 
    return signature

def signature_similarity(data, usersignature):
    datasignature= signature_extractor(data, 1,0)
    score=1
    for key in usersignature:
        try:
            user_keysignature=usersignature[key]
            data_keysignature=datasignature[key]
            probability= key_similarity(user_keysignature, data_keysignature)
            score*= 2*probability
            
            print 'analising key %d, mean: %f, stddev: %f, given mean: %f, probability %f'% (key,user_keysignature[0],user_keysignature[1], data_keysignature[0], probability)
        except:
            print 'no key %d on data signature'%key
    return score

def key_similarity(usersignature, datasignature):
    stddev= usersignature[1]
    difference= abs(usersignature[0]-datasignature[0])
    return norm.cdf(-difference/stddev)
    

def log_key(key, type, time):
    log.append((key,type, time))
    
def save_log(filename, log):
    file=open(filename+'.data.pickle', 'wb')
    pickle.dump(log, file)
    file.close()
    
def open_log(filename):
    try:
        file=open(filename+'.data.pickle','rb')
        log=pickle.load(file)
        file.close()
        return log
    except:
        return []

def save_signature(filename, signature):
    file=open(filename+'.signature.pickle', 'wb')
    pickle.dump(signature, file)
    file.close()

def load_signature(filename):
    try:
        file=open(filename+'.signature.pickle','rb')
        signature=pickle.load(file)
        file.close()
        return signature
    except:
        raise Exception('no such signature file')
    

def callback(key, type, time):
    log_key(key,type,time)

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



goncalo_signature=load_signature('goncalo')
yuna_signature=load_signature('yuna')


mytimingextractor=TimingExtractor(500)
capture_keys.start(mytimingextractor.keypress)
#log= open_log(filename)
#for e in log:
#    mytimingextractor.keypress(e[0],e[1],e[2])

data=mytimingextractor.dwell_times


print "analysing data with goncalo signature"
print signature_similarity(data, goncalo_signature)
print 
print "analysing data with yuna signature"
print signature_similarity(data, yuna_signature)
print 
    
