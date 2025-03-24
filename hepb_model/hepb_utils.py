# This file is part of the HepB Model
#
# Misc utility functions.
# 
# 
import sys
import pandas as pd
import numpy as np

import numba
from numba import int32, int64
from numba.experimental import jitclass

def printf(msg):
    print(msg)
    sys.stdout.flush()


def print_run_summary(model_output_stats_file, burn_in_days):
    """Print basic run stats from the model output stats file.

        Parameters
        ----------
        model_output_stats_file : str
            model output stats file (CSV)
        burn_in_days : float
            days for burn in period to remove from stats
    """
    
    # Read the stats.csv into a pandas data frame to print basic run stats
    stats_df = pd.read_csv(model_output_stats_file)

    # Filter out collected stats during burn in
    subset_df = stats_df[stats_df["tick"] > burn_in_days]

    total_deaths = subset_df.deaths.sum()
    total_overdoses = subset_df.overdoses.sum()
    deaths_averted = subset_df.deaths_averted.sum()
    ems_calls = subset_df.ems_calls.sum()

    printf(
        f'Total Deaths: {total_deaths}, Total Overdoses: {total_overdoses},'
        f' Deaths Averted: {deaths_averted}, EMS Calls: {ems_calls}'
    )


spec = [
    ('mo', int32[:]),
    ('no', int32[:]),
    ('xmin', int32),
    ('ymin', int32),
    ('ymax', int32),
    ('xmax', int32)
]

@jitclass(spec)
class GridNghFinder:

    def __init__(self, xmin, ymin, xmax, ymax, include_center=False):
        if include_center:
            self.mo = np.array([-1, 0, 1, -1, 0, 1, -1, 0, 1], dtype=np.int32)
            self.no = np.array([1, 1, 1, 0, 0, 0, -1, -1, -1], dtype=np.int32)
        else:
            self.mo = np.array([-1, 0, 1, -1, 1, -1, 0, 1], dtype=np.int32)
            self.no = np.array([1, 1, 1, 0, 0, -1, -1, -1], dtype=np.int32)
        
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def find(self, x, y):
        xs = self.mo + x
        ys = self.no + y

        xd = (xs >= self.xmin) & (xs <= self.xmax)
        xs = xs[xd]
        ys = ys[xd]

        yd = (ys >= self.ymin) & (ys <= self.ymax)
        xs = xs[yd]
        ys = ys[yd]

        return np.stack((xs, ys, np.zeros(len(ys), dtype=np.int32)), axis=-1)