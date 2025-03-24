# This file is part of the HepB Model
#
# Hepatocyte agent class
# 
# 

import math

from repast4py import core, schedule, parameters, random
from repast4py.network import DirectedSharedNetwork
from repast4py.schedule import PriorityType

#from .model_statistics import Statistics, LogType
from .constants import *
from .hepb_enums import Status
from .distributions import Distributions

class Hepatocyte(core.Agent):

    """Hepatocyte class is the main model agent with all Hepatocyte behaviors.
    
       Hepatocytes are placed in the shared grid with one cell per grid location.
    
    Attributes
    ----------
    hepb_id : int        
        unique identifier of the person

    status : Status (Enum)
        The cell agents can be in one of the following three discrete states: 
            uninfected susceptible target (T), 
            infected cell in eclipse phase (IE) (i.e., not yet releasing progeny virus), or
            productively infected cell secreting progeny virus (IP)
    

    TODO add in new...    
    """
    
    # NOTE that the ID attribute is not the same as the ID attribute in person data!
    ID = 0  # repast4Py agent class ID for Hepatocyte

    def __init__(self, id, rank):
        """Constructor
        
        Parameters
        ----------
        hepatocyte_data : dict
            dictionary of data for initializing attributes
        rank : int
            rank on which this Hepatocyte is created
        """

        self.hepb_id = id
        self.eclipsed_phase_period = 0        # initially each hepatocyte is health - so no eclipse time
        self.viral_load_produced = 0          # virus produce at time t
        self.first_infectious_status_time = 0  # track the first time the cell is infectious status
        self.next_production = 0            # when will be the next production 
        self.status = Status.SUSCEPTIBLE

        super().__init__(self.hepb_id, Hepatocyte.ID, rank)

        # print(f'HC {self.hepb_id}, rank {rank}')

    def __str__(self):
        return str(self.hepb_id)
 
    def to_str(self) -> str: 
        p_string = str(self.hepb_id) + "\n"

        return p_string
    
    def step(self) -> None:
        tick = schedule.runner().tick()

        # TODO testing random infection process
        # if tick == 5:
        #     if random.default_rng.random() < 0.1 :
        #         self.eclipsed()
        

        self.eclipsed_to_infected_phase_transition()
        
        if self.status == Status.INFECTED:
            self.produce_virus()

    def eclipsed(self) -> None:
        """ Set the cell status to Eclipsed phase
        """
        self.status = Status.ECLIPSED
        eclipse_time = Distributions().getInstance().get_random_eclipse_time()
        self.eclipsed_phase_period = schedule.runner().tick() + eclipse_time
        self.viral_load_produced = 0

    def eclipsed_to_infected_phase_transition(self) -> None:
        # If the cell status is Eclipsed and the transition to infected time is now,
        #  then transition to infected phase.
        if self.status == Status.ECLIPSED:

            tick = schedule.runner().tick()

            if tick == self.eclipsed_phase_period:
                self.infected()
                self.next_production = int(tick + 1)
        
        pass

    def viral_production_rate(self) -> float:
        """ Calculate the amount of virus infected cell can produce 
        """
        tau = self.first_infectious_status_time

        steepness = parameters.params[VIRAL_PRODUCTION_STEEPNESS_GROWTH_CURVE]
        alpha = parameters.params[VIRAL_PRODUCTION_CYCLE_MIDPOINT]

        expF = 1 + math.exp(-1 * steepness * (tau - alpha))

        viral_production = parameters.params[VIRAL_PRODUCTION_STEADY_STATE] / expF

        if viral_production < 0:
            viral_production = 0

        if viral_production > parameters.params[VIRAL_PRODUCTION_STEADY_STATE]:
            viral_production = parameters.params[VIRAL_PRODUCTION_STEADY_STATE]

        return viral_production

    def production_cycle_power_law(self, cycle:int) -> int:
        """ Calculate the production cycle
        """

        power_law_const = parameters.params[VIRAL_PROD_CYCLE_POWER_LAW_CONSTANT]
        power_law_exp = parameters.params[VIRAL_PROD_CYCLE_POWER_LAW_EXPONENT]

        x = power_law_const * math.exp(-1.0 * cycle * power_law_exp)

        return math.ceil(x)

    def produce_virus(self) -> None:
        # if (self.uid_rank == 1):
        #     self.viral_load_produced += 0.025

        tick = schedule.runner().tick()

        if tick == self.next_production:
            # this is the amount of virus the hepatcyte can produce right now
            viral_C = self.viral_production_rate()

            next_period = self.production_cycle_power_law(self.first_infectious_status_time - 1)
            self.first_infectious_status_time += 1  # add one everytime it produce virus
            
            if next_period <= 1 : # means production is every next step
                next_period = 1
            
            self.next_production = int(tick + next_period)

            # if it is less than 1, it means, the production is 1, when it reach to  production time, else, it can be the maximum
            if viral_C < 1 :
                self.viral_load_produced = 1
            else:
                self.viral_load_produced = int(viral_C)   # Discrete integer virus produced
    

    def infected(self) -> None:
        self.first_infectious_status_time = 1
        self.status = Status.INFECTED
        self.eclipsed_phase_period = 0  # Reset to zero
