# SBATCH Script Guide

## What is SBATCH?
[SBATCH](https://slurm.schedmd.com/sbatch.html) is a command-line utility in SLURM (Simple Linux Utility for Resource Management), an open-source cluster management and job scheduling system. You can use SBATCH to submit a job script for execution in a computing cluster. The job script includes the directives and the commands that need to be executed.

## Example SBATCH Script

```bash
#!/bin/bash
#SBATCH --account=username
#SBATCH --ntasks=1
#SBATCH --mem=16G
#SBATCH --time=07:59:59
#SBATCH --gres=gpu:t4:1
#SBATCH --job-name=layout_generator
#SBATCH --mail-user=example@email.com
#SBATCH --mail-type=begin #email when job starts
#SBATCH --mail-type=end #email when job ends
#SBATCH --mail-type=ALL

module load singularity

srun singularity exec --nv -B $SCRATCH $SCRATCH/singularity/readability_optimization/singularity/netviz-graham-v10.sif bash $SCRATCH/netviz/readability_optimization/layout_generator.sh
```



## SBATCH Parameters:

- **`#!/bin/bash`**: This is the shebang line that defines the script to be run using bash shell.

- **`#SBATCH --account=username`**: Specifies the account name that the job should be charged to. Replace "username" with your own account name.

- **`#SBATCH --ntasks=1`**: Defines the number of tasks to be launched. Modify the number as per your requirement.

- **`#SBATCH --mem=16G`**: Specifies the total memory requested for the job.

- **`#SBATCH --time=07:59:59`**: Limits the total run time of the job. Adjust this value according to your job's expected run time. The format is HH:MM:SS.

- **`#SBATCH --gres=gpu:p100:1`**: Requests a specific type of GPU resource (here, one Nvidia P100). Modify the GPU type and count as per your needs.

- **`#SBATCH --job-name=layout_generator`**: Assigns a specific name to the job. Replace "layout_generator" with your preferred job name.

- **`#SBATCH --mail-user=email@address.ccc`**: Defines the user's email address to receive job notifications. Replace it with your email.

- **`#SBATCH --mail-type=begin`**, **`#SBATCH --mail-type=end`**, **`#SBATCH --mail-type=ALL`**: Sets when to send job alerts. In this case, emails will be sent at the beginning, at the end, and for all events of the job. Other options include "fail" (job fails) and "requeue" (job is requeued).

## Command:

- **module load singularity**: Loads the Singularity module, a container platform designed to handle workflows across different compute platforms including HPC, cloud and others.

- **`srun singularity exec --nv -B $SCRATCH $SCRATCH/singularity/readability_optimization/singularity/netviz-graham-v10.sif bash $SCRATCH/netviz/readability_optimization/layout_generator.sh`**: Executes the Singularity command. Modify the paths as per your directory structure and job requirements.
