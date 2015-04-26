import capture_keys
from keystroke_dynamics import Fingerprint, KeystrokeCaptureData

DATA_DIR= "data/"

def get_some_keystrokes():
    print "Please write the following text. When you're finished, press Ctrl-C"
    print "------------------"
    print open("text.txt").read().lower()
    data= KeystrokeCaptureData()
    try:
        capture_keys.start(data.on_key)
    except KeyboardInterrupt:
        pass
    print "\n"
    return data

def create_fingerprint():
    username= raw_input("what's your name? ")
    data= get_some_keystrokes()
    data.save_to_file( DATA_DIR+username )
    fingerprint= Fingerprint.create( data )
    fingerprint.save_to_file( DATA_DIR+username )
    print "Finished creating fingerprint!"

def get_all_fingerprints():
    import os
    files= [DATA_DIR+f for f in os.listdir(DATA_DIR) if f.endswith(Fingerprint.FILE_EXTENSION)]
    fingerprints= map( Fingerprint.load_from_file, files)
    if len(fingerprints)==0:
        raise Exception("No fingerprints available for matching")
    return zip(fingerprints, files)

def match_fingerprint():
    data= get_some_keystrokes()
    data_fingerprint= Fingerprint.create( data )
    for fingerprint,filename in get_all_fingerprints():
        similarity= data_fingerprint.similarity( fingerprint )
        print "similarity with {}: {}".format( filename, similarity )

if __name__=='__main__':
    print "Choose an option:\n  1) create new fingerprint\n  2) match text to a existing fingerprint"
    try:
        option= int(raw_input())
    except Exception:
        print "Bad option"
        exit()
    print "\n\n"
    if option==1:
        create_fingerprint()
    elif option==2:
        match_fingerprint()
    else:
        print "Bad option"

