#!/bin/bash
#SBATCH -p workq
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -c 1
#SBATCH -t 72:00:00
#SBATCH -A 'storage allocation'
#SBATCH -J VASP_automation
#SBATCH -o vasp.out
#SBATCH -e vasp.err

module purge
module load intel-mpi/2021.5.1


export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

echo $SLURM_SUBMIT_DIR
cd   $SLURM_SUBMIT_DIR

time srun -N1 -n64 /YOUR/VASP/EXECUTABLE/LOCATION/vasp_std > vasp_run.out


