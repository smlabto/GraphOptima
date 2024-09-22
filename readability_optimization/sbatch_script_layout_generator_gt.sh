#!/bin/bash
#SBATCH --account=def-primath
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=16G
#SBATCH --time=3:59:59
#SBATCH --job-name=layout_generator

module load apptainer

srun singularity exec --nv -B $SCRATCH $SCRATCH/netviz/readability_optimization/singularity/netviz-graham-v10.sif bash $SCRATCH/netviz/readability_optimization/layout_generator.sh