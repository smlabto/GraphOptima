#!/bin/bash
#SBATCH --account=def-primath
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=3:59:59
#SBATCH --gres=gpu:t4:1
#SBATCH --job-name=layout_evaluator

bash layout_evaluator.sh