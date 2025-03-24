import math, sys
import numpy as np
from mpi4py import MPI

from repast4py import core, schedule, parameters, random, context
from repast4py.space import DiscretePoint as dpt

from .hepb_enums import Status
from .constants import *
from .hepatocyte import Hepatocyte
from .hepb_utils import printf, GridNghFinder

class HBVirus():
    """HBVirus models the Hep B virus activitiy in the bloodstream.
    
       One HBVirus instance is created per rank and is responsible for 
       updating the viral load and infecting Hepatocytes on this rank.
    
    Attributes
    ----------
    total_viral_load : int        
        The HBV viral load on this rank.

    
    

    TODO add in new...    
    """



    def __init__(self, rank:int, comm: MPI.Intracomm, context:context.SharedContext) -> None:
        self.rank = rank
        self.comm = comm
        self.context = context

        world_size = comm.Get_size()

        # The total viral load in the blood, sum across all ranks
        self.total_viral_load = parameters.params[INITIAL_VIRAL_LOAD] / world_size

        self.proportion_infectious_virus = parameters.params[INFECTIOUS_VIRUS_FIRST_DAY]
        self.viral_infection_rate = parameters.params[VIRAL_INFECTION_RATE]

        # Viral load production on this rank
        self.local_viral_load_production = 0

        self.local_susceptible = 0
        self.local_eclipsed = 0
        self.local_infected = 0

        self.grid = self.context.get_projection('grid')

        grid_height = parameters.params[GRID_HEIGHT]
        grid_width = parameters.params[GRID_WIDTH]

        self.ngh_finder = GridNghFinder(0, 0, grid_width, grid_height)

    
    # def step(self) -> None:
    #     self.infect();
    #     self.step_function_viral_proportion();

    #     self.update_viral_load();

    def log_cell_counts(self) -> None:
        """ Log the *local* counts of each Hepatocyte status type

        """
        self.local_cells = self.context.size([Hepatocyte.ID])[Hepatocyte.ID]

        self.local_susceptible = 0
        self.local_eclipsed = 0
        self.local_infected = 0
        for hepatocyte in self.context.agents(Hepatocyte.ID):
            if hepatocyte.status == Status.SUSCEPTIBLE:
                self.local_susceptible += 1
            elif hepatocyte.status == Status.ECLIPSED:
                self.local_eclipsed += 1
            elif hepatocyte.status == Status.INFECTED:
                self.local_infected += 1

    def infect(self) -> None:
        """ infect susciptible hepatocytes - if there are any
            First- determine how many cell to infect- based on BVT
   
        """

        # NOTE the AnyLogic implementation does not infect nearest neighbors like the Mason version.
        # TODO add to model properties
        infect_neighbors = False

        # get heptocytes to infect- this method determine the number of hepatocyte to infect
        n = self.determine_number_to_infect()
        
        # Get a shuffled list of random heptocytes to try and infect (eclipse)
        random_hepatocytes = self.context.agents(Hepatocyte.ID, count = n, shuffle = True)

        # For each randomly selected HC, if its susceptible, then infect it, otherwise if the HC
        #   is already infected, select up to 2 random neighbors and infect them.
        for hepatcyte in random_hepatocytes:
            if hepatcyte.status == Status.SUSCEPTIBLE:
                hepatcyte.eclipsed()
            else:
                if infect_neighbors:
                    pt = self.grid.get_location(hepatcyte)
                    nghs = self.ngh_finder.find(pt.x, pt.y)  # include_origin=True)
                    # print(f'Search origin: {pt.x}, {pt.y}. Radius: {nghs}')

                    at = dpt(0, 0)
                    susceptible_neighs = []
                    for ngh in nghs:
                        at._reset_from_array(ngh)
                        # NOTE We expect that all agents are Hepatocyte, so no need to check type
                        for hc in self.grid.get_agents(at):
                            if hc.status == Status.SUSCEPTIBLE:
                                susceptible_neighs.append(hc)

                    if len(susceptible_neighs) > 0:
                        selected = random.default_rng.choice(susceptible_neighs, 2)
                        for hc in selected:
                            # print(f'Infected neighbor: {hc}')
                            hc.eclipsed()


    def determine_number_to_infect(self) -> int:
        total_cells = self.context.size([Hepatocyte.ID])[Hepatocyte.ID]
        
        total_susceptible = 0
        for hepatocyte in self.context.agents(Hepatocyte.ID):
            if hepatocyte.status == Status.SUSCEPTIBLE:
                total_susceptible += 1

        ratio_susceptible =  total_susceptible / total_cells

        rate_of_infection = self.proportion_infectious_virus * self.viral_infection_rate * self.total_viral_load * ratio_susceptible

        # printf(f'Num suc: {total_susceptible}, total cells: {total_cells}, rate of infection: {rate_of_infection}, rank: {self.rank}')

        # rate is between 0 and 1, randomly return 0 or 1.
        if 0 <= rate_of_infection < 1:
            # rate_of_infection = round(random.default_rng.random())    # NOTE Mason
            rate_of_infection = 1                                       # NOTE AnyLogic


        return math.ceil(rate_of_infection)
    

    def step_function_viral_proportion(self) -> None:
        """ used to calcualte the proportion of infectious virus for first day
        """

        tick = schedule.runner().tick()

        # TODO just schedule this change instead of checking each tick
        if tick < STEPHOUR:
             self.proportion_infectious_virus = parameters.params[INFECTIOUS_VIRUS_FIRST_DAY]
        else: 
            self.proportion_infectious_virus = parameters.params[PROPORTION_INFECTIOUS_VIRUS]

    def degrade_viral_load_rate(self) -> float:
        """ Y = Yo * e^rt  , where 0<r<1, t =1
        """
        # return math.exp(-1.0 * parameters.params[VIRAL_DEGREDATION_RATE])  # NOTE Mason
        return 1.0 - parameters.params[VIRAL_DEGREDATION_RATE]  # NOTE AnyLogic

        
    def update_viral_load(self) -> None:
        tick = schedule.runner().tick()

        if tick > 0:
            self.new_viral_load_production()
            
            # TODO check if schedule priority is better than using MPI barrier
            self.comm.Barrier()

            # Sum the local viral load production across all ranks, storing the result in rank 0
            sum_loads = np.zeros(1, dtype='i') # The sum across ranks
            self.comm.Reduce(np.array([self.local_viral_load_production], dtype='i'), sum_loads, op=MPI.SUM, root=0)

            # TODO check if this can be used instead of Bcast
            # self.comm.Allreduce()

            sum_local_viral_load_production = sum_loads[0]
            
            # Update the total (blood) viral load including temporal degredation just on one rank,
            #    then broadcast it to all other ranks.
            if self.rank == 0:
                # printf(f'rank {self.rank}, sum local viral load: {sum_local_viral_load_production}')
                deg_infe = math.floor(self.total_viral_load * self.degrade_viral_load_rate() )
                self.total_viral_load = deg_infe + sum_local_viral_load_production
                
                world_size = self.comm.Get_size()
                self.total_viral_load = self.total_viral_load / world_size

                data = np.array([self.total_viral_load], dtype='i')
            else:
                data = np.zeros(1, dtype='i')

            # Broadcast the total viral load calculated on rank 0 to all other ranks
            self.comm.Bcast(data, root=0)
            
            self.total_viral_load = data[0]
        
            # if (self.rank == 0):
            # printf(f'Total viral load: {self.total_viral_load}, rank: {self.rank}')

 
    def new_viral_load_production(self) -> None:
        """ Calculate the local viral load production on each rank
            Then sum accross ranks
        """
        viral_load = 0
        
        for hepatocyte in self.context.agents(Hepatocyte.ID):
            viral_load += hepatocyte.viral_load_produced

            # to avoid double counting, once the newly produced virus is counted, 
            # set the value to zero. the idea is once the viirus is relased froom 
            # the cell, it is no more in the cell but in the blook stream.
            hepatocyte.viral_load_produced = 0

        # TODO check for sync issues if all ranks will use the current local_viral_load_value
        self.local_viral_load_production = int(viral_load)

        # printf(f'rank {self.rank}, local viral load: {self.local_viral_load_production}')

        # load = np.zeros(1, dtype='float64')

        # self.comm.Reduce(np.array([self.local_viral_load], dtype='float64'), load, op=MPI.SUM, root=0)

        # printf(f'rank {self.rank} , local viral load: {self.local_viral_load}, total viral load {self.total_viral_load}')

        # return int(viral_load)

        

        