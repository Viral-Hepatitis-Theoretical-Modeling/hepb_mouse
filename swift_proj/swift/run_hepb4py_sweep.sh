
#! /usr/bin/env bash
set -eu

if [ "$#" -ne 2 ]; then
  script_name=$(basename $0)
  echo "Usage: ${script_name} EXPERIMENT_ID CONFIG_FILE(e.g. ${script_name} experiment_1 model.props)"
  exit 1
fi

# uncomment to turn on swift/t logging. Can also set TURBINE_LOG,
# TURBINE_DEBUG, and ADLB_DEBUG to 0 to turn off logging
# export TURBINE_LOG=1 TURBINE_DEBUG=1 ADLB_DEBUG=1
export EMEWS_PROJECT_ROOT=$( cd $( dirname $0 )/.. ; /bin/pwd )
# source some utility functions used by EMEWS in this script
source "${EMEWS_PROJECT_ROOT}/etc/emews_utils.sh"

export EXPID=$1
export TURBINE_OUTPUT=$EMEWS_PROJECT_ROOT/experiments/$EXPID
check_directory_exists

# TODO edit the number of processes as required.
export PROCS=12

# TODO edit QUEUE, WALLTIME, PPN, AND TURNBINE_JOBNAME
# as required. Note that QUEUE, WALLTIME, PPN, AND TURNBINE_JOBNAME will
# be ignored if the MACHINE variable (see below) is not set.
#export QUEUE=bdwall
#export PROJECT=naerm
export PROJECT=condo
export QUEUE=dis
export WALLTIME=06:00:00
export PPN=18
export TURBINE_JOBNAME="${EXPID}_job"

#export PYTHONPATH=$EMEWS_PROJECT_ROOT/python:$EMEWS_PROJECT_ROOT/ext/EQ-Py
# NOTE The python path should include the project root to reference hepcep_model
export PYTHONPATH=$EMEWS_PROJECT_ROOT/../

# TODO edit command line arguments as appropriate
# for your run. Note that the default $* will pass all of this script's
# command line arguments to the swift script.
CMD_LINE_ARGS="$*"

CONFIG_FILE=$EMEWS_PROJECT_ROOT/../data/$2

# Comment for local runs
# Bebop use srun
# export TURBINE_LAUNCHER=srun

# Empty for local runs
# Bebop use slurm
#MACHINE="slurm"
MACHINE=""

if [ -n "$MACHINE" ]; then
  MACHINE="-m $MACHINE"
fi

# Add any script variables that you want to log as
# part of the experiment meta data to the USER_VARS array,
# for example, USER_VARS=("VAR_1" "VAR_2")
USER_VARS=()
# log variables and script to to TURBINE_OUTPUT directory
log_script

# echo's anything following this standard out
set -x

swift-t -n $PROCS $MACHINE -p \
    $EMEWS_PROJECT_ROOT/swift/run_sweep.swift \
    -f="$EMEWS_PROJECT_ROOT/data/upf_test.txt" \
    -config_file=$CONFIG_FILE \
    $CMD_LINE_ARGS
