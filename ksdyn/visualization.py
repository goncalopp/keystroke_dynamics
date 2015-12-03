from ksdyn.core import DictTree
from ksdyn.model import GaussianAnomalyModel

import numpy as np
import matplotlib
from matplotlib import pyplot

def synthesize_data( normal_model, n=10000 ):
    d= normal_model
    return np.random.normal( loc= d.mean, scale=d.stddev, size=normal_model.nsamples)

def normal_to_bar( normal_model ):
    '''returns bottom and top of a bar'''
    d= normal_model
    delta= d.stddev * 2
    return d.mean-delta, d.mean+delta

def visualize_normal_composite( composite, color='blue', offset=0.0, width=0.8, show=True ):
    '''visualizes a composite model composed of normal models'''
    key_list= [composite[k] for k in sorted(composite.keys())]
    assert all( [isinstance( key, GaussianAnomalyModel ) for key in key_list])
    heights, bottoms= zip(*map(normal_to_bar, key_list))
    labels= [ k.name for k in key_list ]

    xs= np.arange(len(heights)) + offset
    pyplot.bar(xs, heights, bottom=bottoms, color=color, width=width )
    pyplot.setp( pyplot.gca(), label= labels )
    if show:
        pyplot.show()

def visualize_normal_composites( composites, show=True ):
    COLORS= ('red', 'orange','yellow','green', 'blue', 'violet')
    n= len(composites)
    width= 0.9-(0.1*n)
    common= DictTree.intersect( *composites )
    colors= COLORS[:n]
    for i,c,color in zip(range(n),common, colors):
        visualize_normal_composite( c, color=color, show=False, offset=i*0.1, width=width)
    if show:
        pyplot.show()


