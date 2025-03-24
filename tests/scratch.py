# import csv
# 
# with open('data/viral_kinetics/acute-infection-clearance.csv', 'r') as file:
#     reader = csv.reader(file)
    
#     loads = {row[0]:row[1:len(row)]for row in reader}
    
# import json
# with open('result.json', 'w') as fp:
#     json.dump(loads, fp, indent=4)

import numpy as np

def find_closest(x:np.array, val):
    """ Find the closest valuue in a numpy array and return the index and value.

    Parameters
    ----------
    x : np.array
        An array of values.
    val : the value to find in the array
    
    Returns 
    -------
    index,value
        the pair of index and closest value in the array to val.
    """
    idx = np.abs(x - val).argmin()
    return idx, x[idx]

data = np.genfromtxt('data/viral_kinetics/transmission_probability.csv', delimiter=',', skip_header=True)

idx, val = find_closest(data[:,0], 30003)

print(idx)
print(val)


