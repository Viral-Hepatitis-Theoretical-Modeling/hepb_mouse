# This file is part of the HepB Model
#
# Logger classes for storing and writing event log files.
# 
# 

import csv, os, math
from datetime import datetime

from repast4py import parameters

from .hepb_enums import *
from .constants import *


class Statistics:
    """Statistics class records changes in all agent attributes and compiles
    additional summary aggregate statistics.
    
    Attributes
    ----------
    __instance : Statistics
        Statistics singleton
    events_writer : csv.writer
        CSV writer for events log data
    stats_writer : csv.writer
        CSV writer for stats log data
    
    """
    
    __instance = None
   
    @staticmethod 
    def getInstance():
        return Statistics.__instance
   
    def __init__(self):
        """Constructor
        
        Parameters
        ----------
        
        """
        
        Statistics.__instance = self
        
        output_dir = parameters.params[OUTPUT_DIRECTORY]
        # output_dir = os.path.join(output_dir, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        stats_fname = os.path.join(output_dir, 'run_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_' + parameters.params[STATS_OUTPUT_FILE])
        
        self.stats_file = open(stats_fname,'w', newline='')
        self.stats_writer = csv.writer(self.stats_file)

        # Write headers
        self.stats_writer.writerow(["run","tick","susceptible","eclipsed","infected","viral load (log)"])

    # TODO Performance Profiling ~25% CPU here.
    def record_stats(self, tick, run, num_susciptible, num_eclipsed, num_infected, total_viral_load):
        """Writes any cached stats to file for each of the event loggers.
        
        Parameters
        ----------
        tick : float
            the model tick
        run : int
            the model run number
        """
        if total_viral_load > 0:
            viral_load_log = math.log10(total_viral_load)
        else:
            viral_load_log = 0
        
        
        # Write the summary stats and aggregate stats for this tick
        self.stats_writer.writerow([str(run), str(tick), str(num_susciptible), str(num_eclipsed), str(num_infected), str(viral_load_log) ])
                        
        # Flushing files ensures incremental save
        self.stats_file.flush()

            
    def close(self):
        """Flush and close the log files
        """

        self.stats_file.flush()
        self.stats_file.close()

        Statistics.__instance = None
        