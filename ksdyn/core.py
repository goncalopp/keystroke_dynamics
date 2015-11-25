import pickle
from abc import ABCMeta, abstractmethod

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
 
