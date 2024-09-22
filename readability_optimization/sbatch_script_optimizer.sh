#!/bin/bash
#SBATCH --account=def-primath
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=3:59:59
#SBATCH --job-name=optimizer

module load apptainer

srun singularity exec --nv -B $SCRATCH $SCRATCH/netviz/readability_optimization/singularity/netviz-graham-v10.sif bash $SCRATCH/netviz/readability_optimization/optimizer.sh