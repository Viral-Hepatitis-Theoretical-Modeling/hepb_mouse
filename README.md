# hepb4Py
Repast4Py port of HepBV


## Running the model from command line

The HepB Model can be run as a python module by either adding it to
the `PYTHONPATH` environment variable.

Create a work folder that is not the same as the HepB root folder to avoid
issues with module paths.  Use for example `Hepb/swift_proj`, or `HepCEP/local_proj`

### For single run
```
python3 -m hepb_model ../data/model_props.yaml
```

Optional properties can be provided via a json string, as:

```
python3 -m hepb_model ../data/model_props.yaml '{"stop.at":50}'
```

:warning: The model currently does not make use of mulit-rank parallelism, so using mpi for
a local run will just result in duplicate runs.

### For MPI runs across multiple ranks
```
mpirun -n 16 python3 -m hepb_model ../data/model_props.yaml
```

## Profiling with cProfile
While still in e.g. local_proj folder, run:

```
python3 -m cProfile -o output.pstats  -m hepb_model ../data/model_props.yaml '{"stop.at":100}'
```

### Viewing profiling results
The cProfile stats file is plain text but can be visualized using [gprof2dot](https://github.com/jrfonseca/gprof2dot).
gprof2dot can be installed via pypi, and requires graphviv via apt install, and optionally a image viewer like eog:
```
apt install graphviz eog
pip install gprof2dot
```

To generate a scalable SVG image of the profile results, run the command, assuming the profile output file
from cProfile is named output.pstats, and you want tp ise eog (or similar) to view the output.svg.
```
gprof2dot -f pstats output.pstats | dot -Tsvg -o output.svg && eog output.svg
```


## Running unit tests
In the project root folder call:

```
python3 -m unittest -v tests/test.py
```

## Running the model from python code
Import the jccm_module and call the jccm.run() with the MPI Comminicator,
model.props file and optional additinal params, see `__main__.py` for usage.

```python
import hepb_model as hepb

mpi4py_comm = hepb_model.get_task_comm(use_world=True)
hepb_model.run(mpi4py_comm, props, params)
```

## Installing Repast4py via pypi or a local repository
To use the release version of repast4py, simply install via:

```
env CC=mpicxx pip install repast4py
```

To use a local repository, e.g. a development branch, switch to the root of the
git repo, and use the command:

```
env CC=mpicxx pip install -e .
```

and note that the '.' signifies the current dir.  

## Running the model from swift-t emwes workflow
The swift-t script `swift_run_sweep.swift` will run the model via swift-t 
`python_parallel_persist`:

```
z[i] = @par=1 python_parallel_persist(model_code, "repr(hepb_model.get())");
```

where `model_code` is a python snipped similar to above for running via python.

### Local Runs
* For UPF sweeps use `run_hepcep4py_sweep.sh
  - Change the PROCS, QUEUE, etc as needed
  - Set MACHINE=""
  - Comment #TURBINE_LAUNCHER=srun
  - Set the UPF file using the -f argument

### Bebop
* Source the `bebop_module_load_hepcep.sh` to load the required modules on bebop
* For UPF sweeps use `run_hepcep4py_sweep.sh
  - Change the PROCS, QUEUE, etc as needed
  - Set MACHINE="slurm"
  - Set TURBINE_LAUNCHER=srun
  - Set the UPF file using the -f argument
