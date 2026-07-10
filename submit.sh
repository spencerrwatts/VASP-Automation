#!/bin/bash
#SBATCH -p gpu
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -c 1
#SBATCH -t 72:00:00
#SBATCH -A hpc_te_mater_1
#SBATCH -J EuAl2Cl8
#SBATCH -o vasp.out
#SBATCH -e vasp.err
#SBATCH --mail-user=swatt15@lsu.edu

module purge
module load intel-mpi/2021.5.1


export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

echo $SLURM_SUBMIT_DIR
cd   $SLURM_SUBMIT_DIR

time srun -N1 -n64 /project/svyatium/vasp/vasp.6.4.1/bin/vasp_std > vasp_run.out


