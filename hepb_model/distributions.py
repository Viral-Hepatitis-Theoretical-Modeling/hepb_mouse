# This file is part of the HepB Model
#
# Random Distributions
# 
# 

from repast4py import parameters, random

from .constants import *

class Distributions:
    """Distributions class holds statistical distributions references.
    
    Attributes
    ----------
    __instance : Distributions
        Distributions singleton

    """
    
    __instance = None
   
    @staticmethod 
    def getInstance():
        return Distributions.__instance
   
    def __init__(self):
        """Constructor
        
        Parameters
        ----------
        
        """
        
        # NOTE repast4py random.init() will set the numpy generator seed using the random.seed parameter

        Distributions.__instance = self


    def get_random_eclipse_time(self) -> int:
        
        min = parameters.params[ECLIPSED_TO_INFECTED_PHASE_TRANSITION_MIN]
        max = parameters.params[ECLIPSED_TO_INFECTED_PHASE_TRANSITION_MAX]

        return random.default_rng.integers(min,max)
        

