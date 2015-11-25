try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
 
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = ''

setup(
    name = "ksdyn",
    version = "0.0.0",
    url = 'http://github.com/goncalopp/keystroke_dynamics',
    license = 'CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
    description = "Keystroke dynamics",
    long_description = '',
    author = 'goncalopp',
    author_email = '',
    packages = ['ksdyn'],
    classifiers = \
        [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        ]
)
