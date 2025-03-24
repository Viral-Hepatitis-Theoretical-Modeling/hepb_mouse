# This file is part of the HepB Model
#
# Script containing HepB Model main loop
# 
# 

from mpi4py import MPI
import sys, os

import numpy as np
import networkx as nx
from pathlib import Path
from datetime import datetime
# import json
import functools
from timeit import default_timer as timer
# import pandas as pd 
import yaml

from repast4py.parameters import init_params
from repast4py import core, schedule, context, parameters, random, space
from repast4py.space import BorderType, OccupancyType, GridStickyBorders, GridPeriodicBorders
from repast4py.space import DiscretePoint as DPt

from .constants import *
from .hepatocyte import Hepatocyte
from .hbvirus import *
from .hepb_enums import *
from .hepb_utils import printf, GridNghFinder
from .model_statistics import Statistics
from .distributions import Distributions

model = None

def write_props(dir):
    """Save the model props to a file in the output folder

        Parameters
        ----------
        dir : str
            the model output directory
    """

    fname = os.path.join(dir,'model_props.yaml')

    with open(fname, 'w') as f:
        yaml.dump( parameters.params, f, default_flow_style=False) 

class Model:
    """The HepB Model class.

    """
    def __init__(self, comm: MPI.Intracomm):
        self.comm = comm
        self.context = context.SharedContext(comm)
        self.rank = self.comm.Get_rank()

        world_size = comm.Get_size()

        # # Viral load on this rank
        # self.local_viral_load = 0
            
        
        # TODO model out file name for non-distributed runs, eg ME runs
        self.run_number = 0
        if 'run.number' in parameters.params: 
            self.run_number = parameters.params['run.number']
        
        start = timer()

        # Sample the random instance lots of times to check for proper seeding.
        random.default_rng.random(10000)
        d = random.default_rng.random(1)

        if self.rank == 0:
            printf(f'HepB Model Initialization... Run # {self.run_number}.  Random seed: {parameters.params["random.seed"]}, rand = {d}')
            printf(f'Ranks: {world_size}')
        
        # Schedule the model step interval and end time
        self.runner = schedule.init_schedule_runner(comm)
        self.runner.schedule_repeating_event(1, 1, self.step)
        self.runner.schedule_stop(parameters.params[RUN_TIME])
        

        output_dir = parameters.params[OUTPUT_DIRECTORY]
        
        if self.rank == 0:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

        data_dir = parameters.params[DATA_DIR]

        tick = schedule.runner().tick()

        Distributions() # Initialize Distributions
        Statistics()    # Initialize Statistics
    
        grid_height = parameters.params[GRID_HEIGHT]
        grid_width = parameters.params[GRID_WIDTH]

        box = space.BoundingBox(0, grid_width, 0, grid_height, 0, 0)

        self.grid = space.SharedGrid('grid', bounds=box, borders=BorderType.Sticky, 
                                     occupancy=OccupancyType.Single,
                                     buffer_size=2, comm=comm)
        
        self.context.add_projection(self.grid)
        
        local_bounds = self.grid.get_local_bounds()

        # printf(f'rank: {self.rank}, x: {local_bounds.xmin},  {local_bounds.xmin+local_bounds.xextent}')
        # printf(f'rank: {self.rank}, y: {local_bounds.ymin},  {local_bounds.ymin+local_bounds.yextent}')

        # Create the individual Hepatocyte agents and add them to the grid
        id = 0
        for i in range(local_bounds.xmin, local_bounds.xmin+local_bounds.xextent):
            for j in range (local_bounds.ymin, local_bounds.ymin+local_bounds.yextent):
                hc = Hepatocyte(id, self.rank)
                self.context.add(hc)
                self.grid.move(hc, DPt(i,j))
                id += 1


        # Create the HB Virus agent

        self.hb_virus = HBVirus(self.rank, comm, self.context)

        # self.ngh_finder = GridNghFinder(0, 0, box.xextent, box.yextent)

        # agent = grid.get_agent(space.DiscretePoint(0, 0))


        if self.rank == 0:        
            write_props(output_dir)

        self.runner.schedule_end_event(self.at_end)

        if self.rank == 0:
            stop = timer()
            printf("Model init time: " + str(stop - start) + "s.")

    def step(self):
        """Main model step behavior.  This method controls the sequence of model
        behavior such as person steps.
        """
        
        tick =  schedule.runner().tick()

        if self.rank == 0 and tick % 25 == 0:
            printf(f'Tick: {tick}')

        # Update the HBVirus instance on all ranks
        self.hb_virus.log_cell_counts()

        self.log_stats(tick)  # Aggregate stats across ranks and save data

        self.hb_virus.infect()
        self.hb_virus.step_function_viral_proportion()
        self.hb_virus.update_viral_load()

        # Update the Hepatocytes on all ranks
        for hepatocyte in self.context.agents(Hepatocyte.ID):
            hepatocyte.step()
        
    def log_stats(self, tick):
        sum_susceptible = np.zeros(1, dtype='i') 
        sum_eclipsed = np.zeros(1, dtype='i') 
        sum_infected = np.zeros(1, dtype='i') 
        self.comm.Reduce(np.array([self.hb_virus.local_susceptible], dtype='i'), sum_susceptible, op=MPI.SUM, root=0)
        self.comm.Reduce(np.array([self.hb_virus.local_eclipsed], dtype='i'), sum_eclipsed, op=MPI.SUM, root=0)
        self.comm.Reduce(np.array([self.hb_virus.local_infected], dtype='i'), sum_infected, op=MPI.SUM, root=0)

        if self.rank == 0:
            # Sum of viral load across all ranks
            # NOTE just multiply one rank x world size since viral load is shared across ranks
            total_viral_load = self.hb_virus.total_viral_load * self.comm.Get_size()
            Statistics.getInstance().record_stats(tick, 
                                                  self.run_number, 
                                                  sum_susceptible[0], 
                                                  sum_eclipsed[0], 
                                                  sum_infected[0],
                                                  total_viral_load)

    

    def run(self):
        self.runner.execute()            
                

    def at_end(self):
        """Behaviors to be executed at model end, such as clean up.
        """

#        events_filename = Statistics.getInstance().event_file.name
#        stats_filename = Statistics.getInstance().stats_file.name

#        Statistics.getInstance().close()

#        print_run_summary(stats_filename, self.burnin_period_days)

        if (self.rank == 0):
            printf("Run Ended.")

        # TODO use model.props to save to other formats

        # TODO converting the events CSV to parquet pos run is more efficient for
        #      compressing to smaller file size compared with the on-the-fly
        #      JCCM pyarrow logger.

        # Convert the events CSV to parquet and delete the CSV
        #event_df = pd.read_csv(events_filename)
        #event_df.to_parquet(events_filename.replace('.csv','.parquet')) #,compression='gzip')
        
        # event_df.to_feather('events.feather')

        #os.remove(events_filename)  # delete the csv file


def run(mpi4py_comm, config_file, additional_params):
    """Run the model with provided parameters. Note that swift-t scripts call
       this run method and provide it's own MPI Comm object, so don't hardcode
       the MPI Comm instance here.
        
        Parameters
        ----------
        mpi4py_comm : mpi4py.MPI.Intracomm
            An MPI communicator instance
        config_file : str
            The model config (props) file that contains model property
            names and values delimitted by a '=' symbol.
        additional_params str
            String of aditional params in JSON string format, e.g.
            '{"Name":"Joe", "Age":34}'

    """

    init_params(config_file, additional_params)
    
    # NOTE repast4py random.init() will set the numpy generator seed using the random.seed parameter
   
    # The config_file parent is the default data dir
    # TODO it would be better to set the data dir in the config file perhaps
    config_path = Path(config_file)
    data_dir = str(config_path.parent)

    parameters.params[DATA_DIR] = data_dir

    global model
    model = Model(mpi4py_comm)

    if model.rank == 0:
        start = timer()

    model.run()

    if model.rank == 0:
        stop = timer()
        printf("Model run time: " + str(stop - start) + "s.")

    global result
    result = "Done."  # NOTE returned to swift-t to indicate run finished.
  
def get():
    global result
    return result