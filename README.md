# Hepatitis B virus (HBV) Mouse Model

## About HBV Model
HBV Mouse is a validated agent-based model (ABM) of Hepatitis B virus (HBV) infection kinetics in 
mice developed in [Repast4Py](https://repast.github.io/repast4py.site/index.html).

HBV infection kinetics in immunodeficient mice reconstituted with humanized livers from inoculation to 
steady state is highly dynamic despite the absence of an adaptive immune response. To capture the 
multiphasic viral kinetic patterns, we developed an agent-based model that includes intracellular virion
production cycles reflecting the cyclic  nature of each individual virus lifecycle. The model fits the 
data well predicting an increase in  production cycles initially starting with a long production cycle of 
1 virion per 20 hours that  gradually reaches 1 virion per hour after approximately 3–4 days before 
virion production  increases dramatically to reach to a steady state rate of 4 virions per hour per cell. 
Together,  modeling suggests that it is the cyclic nature of the virus lifecycle combined with an initial 
slow but increasing rate of HBV production from each cell that plays a role in generating the  bserved 
multiphasic HBV kinetic patterns in humanized mice.

**Schematic diagram of the HBV Mouse Model**<br>
(A) The human hepatocytes can be only in one of the following three phases at a given time; T = uninfected 
cells which are termed as target or susceptible cells, IE = HBV-Infected cells in eclipse phase (i.e., not 
yet releasing virions), IP = productively HBV-infected cells (i.e., actively releasing virions). The free 
virus in blood, V, is composed of infectious and non-infections virions. The parameter ρ represents the 
fraction of virions that are infectious, β represents the infection rate constant, O represents eclipse 
phase duration, c, represents viral clearance from blood and P(τ) (Eq 1) represents virion secretion from 
IP. 

(B) Schematic diagram of viral production cycle for an individual infected human hepatocyte. P(τ) is 
the number of virions produced by an infected cell, and l(τ)) is the time interval between production 
cycle (h). The virions were initially released by IP starting with a long production cycle of 1 virion per 
cell (Stage 1: ~0–2.5 days) that gradually reaches a production of 2 virions per cell with a shorten 
production cycle (Stage 2: ~2.5–3 days) and then proceeds to 3 virions per cell (Stage 3: ~3–4 days) before 
virion production increases to reach to a steady state production rate of 4 virions per hour per cell (Stage 4: ~ 4 days onwards).

<img src="doc/Mouse%20ABM.jpg" width="900">

Further details on the mouse model theory and parameters are described in:

>**Modeling suggests that virion production cycles within individual cells is key to  understanding acute 
hepatitis B virus  infection kinetics**. Hailegiorgis A, Ishida Y, Collier N, Imamura M, Shi Z, Reinharz V, 
et al. (2023).  PLoS Comput Biol 19(8): e1011309. https://doi.org/10.1371/journal.pcbi.1011309

The Repast4Py toolkit is described in:

>**Distributed Agent-Based Simulation with Repast4Py**. N. Collier and J. Ozik, 2022 Winter Simulation 
Conference (WSC), Singapore, 2022, pp. 192-206, https://doi.org/10.1109/WSC57314.2022.10015389

## Acknowledgements
This work was supported by funding of the United States National Institutes of Allergy and Infectious 
Diseases (Grant numbers R01AI144112 and R01AI146917), the Japan Agency for Medical Research and 
Development (AMED grant 19fk0210020h0003), the Promotion of Joint International Research (Fostering 
Joint International Research) from Japan Society for the Promotion of Science (Grant number: 17KK0194), 
and by the U.S. Department of Energy under contract number DE-AC02-06CH11357, and was completed with 
resources provided by the Laboratory Computing Resource Center at Argonne National Laboratory (Bebop 
cluster). The research presented in this paper is that of the authors and does not necessarily reflect 
the position or policy of the funding agencies or any other organization.


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
* For UPF sweeps use `run_hepcep4py_sweep.sh`
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
