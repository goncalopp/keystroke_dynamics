import pickle
import numpy as np
import scipy.stats
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
        with open(filename+self.FILE_EXTENSION, 'wb') as f:
            self._serialize_to_file( f )

    @classmethod
    def load_from_file( cls, filename):
        import os
        if not os.path.exists(filename):
            filename+=cls.FILE_EXTENSION
        with open(filename, 'rb') as f:
            instance= cls._deserialize_from_file( f )

        load_error=None
        if not isinstance( instance, cls ):
            load_error= 'Unexpected instance type'
        elif instance._class_version!=cls.CLASS_VERSION:
            load_error= 'Class version mismatch (expected "{}", got "{}")'.format( cls.CLASS_VERSION, instance._class_version)
        if load_error:
            raise TypeError("Failed to load serialized data from {}: {}".format(filename, load_error))

        return instance

    @classmethod
    def load_from_dir( cls, directory ):
        import os
        d= directory
        filenames= [f for f in os.listdir(d) if f.endswith(cls.FILE_EXTENSION)]
        path_names= [os.path.join(d,f) for f in filenames]
        bare_names= [fn.rstrip(cls.FILE_EXTENSION) for fn in filenames] #without extension
        instances= map( cls.load_from_file, path_names)
        return dict(zip(bare_names, instances))

    def _serialize_to_file( self, f ):
        pickle.dump(self, f)

    @classmethod
    def _deserialize_from_file( cls, f ):
         return pickle.load(f)

 
class KeystrokeCaptureData(KeypressEventReceiver, VersionedSerializableClass):
    '''Recorded data of actual keystrokes pressed by a user'''
    FILE_EXTENSION=".keypresses"
    CLASS_VERSION= 0

    def __init__(self, existing_data=None):
        VersionedSerializableClass.__init__(self)
        self.log= list(existing_data) if existing_data else []

    def on_key(self, key, event_type, time_ms):
        '''Append a keypress event to this capture data'''
        self.log.append( (key, event_type, time_ms) )

    def feed(self, event_receiver):
        '''feeds this data into a KeypressEventReceiver.
        Returns the event_receiver'''
        for event in self.log:
            event_receiver.on_key( *event )
        return event_receiver

    def _serialize_to_file( self, f ):
        f.write( str(self.log) )

    @classmethod
    def _deserialize_from_file( self, f ):
        from ast import literal_eval
        data= literal_eval(f.read())
        return KeystrokeCaptureData(data)

class InsufficientData(ValueError):
    '''Raised when there is insuficient data to perform a given operation.
    An example would be a low number of samples for normal distribution estimation'''
    pass

class GaussianDistribution(object):
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
        stddev= max( mean*0.01, stddev ) #avoid stddev==0
        return mean, stddev, nsamples

    def similarity( self, other_normal ):
        '''quick-and-dirty hack. don't take this too seriously'''
        stddev= (self.stddev + other_normal.stddev) / 2.0
        difference= abs(self.mean - other_normal.mean)
        return 2*scipy.stats.norm.cdf(-difference/stddev)

    def similarity_number( self, number ):
        stddev= self.stddev
        difference= abs(self.mean - number)
        return 2*scipy.stats.norm.cdf(-difference/stddev)

    def __repr__(self):
        return "{}({:.2f}, {:.2f}, {})".format( self.__class__.__name__, self.mean, self.stddev, self.nsamples )
    
class Named(object):
    '''Something that has a name'''
    __metaclass__=ABCMeta

    def __init__(self, name):
        self.name= str(name)

    def __repr__( self ):
        return "{}( {} )".format( self.__class__.__name__, self.name )
         

class DictTree(dict, Named):
    '''A dict that can have other DictTree objects as values. 
    Basically, a arbitrary tree that can have any object as a leave.'''
    IGNORE_CHILD='IGNORE_CHILD'
    def __init__( self, name, children=() ):
        '''If this DictTree is a child of another (its parent), NAME will be the key used to identify it in the parent dict.'''
        Named.__init__(self, name)
        for i,c in enumerate(children):
            c_name= c.name if isinstance(c, DictTree) else self._leaf_name(c, i)
            self[c_name]=c

    def _leaf_name(self, leaf, default=""):
        try:
            return leaf.name #this might not make sense, depending on the leaf. DictTree subclasses can override this method
        except AttributeError:
            return default

    @classmethod
    def intersect( cls, *trees  ):
        '''Given N DictTrees, returns N DictTrees, such that
        each outputed tree is a exact copy of the input, but only
        contains children whose names (keys) appear on *all* trees'''
        recursive=True
        common_names= reduce(set.intersection, [set(f.keys()) for f in trees])
        def get_childs( child_name ):
            '''returns the child with child_name for every tree'''
            childs= [tree[child_name] for tree in trees]
            if recursive and childs and isinstance(childs[0], DictTree):
                return cls.getCommonFeatures( childs )
            else:
                return childs
        all_childs= zip(*map( get_childs, common_names ))
        return [cls(tree.name, childs) for tree,childs in zip(trees, all_childs)]

    @staticmethod
    def _isleave( x ):
        return not isinstance(x, DictTree)

    @classmethod
    def map( cls, f_leave, *trees ):
        def map_child( *c ):
            return f_leave(*c) if DictTree._isleave(c[0]) else cls.map( f_leave, *c) 
        old_children= zip(*(t.values() for t in trees))
        children= [map_child(*cs) for cs in old_children ]
        filtered_children= filter( lambda x: x is not cls.IGNORE_CHILD, children )
        return cls( trees[0].name, filtered_children )

    def reduce( self, reduce_f ):
        return reduce(reduce_f, (c if DictTree._isleave(c) else c.reduce(reduce_f) for c in self.values()))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)
