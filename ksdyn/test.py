import unittest
import random

from ksdyn.core import KeystrokeCaptureData, KeypressEventReceiver as KER
from ksdyn.sugar import create_fingerprint_from_capture_data
from ksdyn.model import FingerprintDatabase
from ksdyn import example

random.seed(0) #reproducible tests, at least for the same python version

class SyntheticKeystrokes(KeystrokeCaptureData):
    def __init__(self):
        super(SyntheticKeystrokes, self).__init__()
        time= 0
        n_keypresses= 100
        for _ in range(n_keypresses):
            keycode= random.randint(25,45)
            self.on_key( keycode, KER.KEY_DOWN, time)
            time+= random.randint(40,120)
            self.on_key( keycode, KER.KEY_UP, time)





class SystemTest(unittest.TestCase):
    def test_system(self):
        ks1= SyntheticKeystrokes()
        ks2= SyntheticKeystrokes()
        f1= create_fingerprint_from_capture_data( 'f1', ks1 )
        f2= create_fingerprint_from_capture_data( 'f2', ks2 )
        db= FingerprintDatabase( fingerprints=(f1,f2) )
        self.assertEqual( db.best_match(f1), f1)
        self.assertEqual( db.best_match(f2), f2)


if __name__ == '__main__':
    unittest.main()

