# Setting up cuGraph layout generators on an HPC cluster using Singularity

This guide illustrates the process of setting up cuGraph, a GPU accelerated graph layout library, on the Graham cluster
of the Digital Research Alliance of Canada (formerly, Compute Canada) using Singularity.

> Note: The Singularity has now been renamed to Apptainer, and the steps in the tutorial works for both Singularity and
> Apptainer.

## Pre-requisites

Before starting, ensure that you have access to a computer with **root access**. Root access is necessary to create a
Singularity instance (a `.sif` file ).

## Download the GraphOptima Virtual Container
You can download the `.sif` container file from the following
link: https://drive.google.com/file/d/1XewLuZst3iK4BwxTvay8IjMfDrh8eL2f/view?usp=sharing

>Note: after you have downloaded the container file, you will still need to upload the container file to the HPC, 
Skip steps 1–3 and jump to step 4.

You can also download the container by running the following bash script: 
```bash
cd $SCRATCH/netviz/readability_optimization/
bash build_singularity.sh
```

## Steps to create GraphOptima Virtual Container

### 1. Install Singularity

Install Singularity on your machine following the guidelines provided in
the [Singularity documentation](https://sylabs.io/guides/latest/user-guide/quick_start.html).

### 2.Create a definition file containing the installation commands.

Depending on the cuda version on the GPU nodes of your cluster, selecting one `def` file to build a container.

#### CUDA 11.8

Save the following script as a `.def` file:

```sh
Bootstrap: docker
From: rapidsai/notebooks:24.04-cuda11.8-py3.11

%post
    apt install git -y
    . /opt/conda/etc/profile.d/conda.sh
    conda activate base
    conda config --set remote_read_timeout_secs 600.0
    conda install --solver=libmamba pytorch torchvision torchaudio pytorch-cuda=12.1 jupyterlab ipython graph-tool pymoo filelock pyyaml pygraphviz -c pytorch -c nvidia -c conda-forge -q -y

%labels
    Version v10.2.0
    Author maxjingweizhang@ryerson.ca

%help
    A integrated virtual enviroment for GraphOptima: Framework for Optimizing Graph Layout and Readability 
    on Compute Canada's Graham cluster.
```

#### CUDA 12.0

Save the following script as a `.def` file:

```sh
Bootstrap: docker
From: rapidsai/notebooks:24.04-cuda12.0-py3.11

%post
    apt install git -y
    . /opt/conda/etc/profile.d/conda.sh
    conda activate base
    conda config --set remote_read_timeout_secs 600.0
    conda install --solver=libmamba pytorch torchvision torchaudio pytorch-cuda=12.1 jupyterlab ipython graph-tool pymoo filelock pyyaml pygraphviz -c pytorch -c nvidia -c conda-forge -q -y

%labels
    Version v10.2.0
    Author maxjingweizhang@ryerson.ca

%help
    A integrated virtual enviroment for GraphOptima: Framework for Optimizing Graph Layout and Readability 
    on Compute Canada's Graham cluster.
```

### 3. Create a Singularity instance

Navigate to the repository folder and run the following command to create a Singularity instance

```sh
sudo singularity build netviz-graham-v10.sif netviz-graham-v10.def
```

This command will generate a Singularity instance file (.sif) from a definition file (.def). The definition file is
based on the Docker file from the original cuGraph repository on NVIDIA and contains additional libraries needed for the
system to operate.

### 4. Transfer the Singularity Instance to the HPC cluster

The newly created Singularity instance file will have a non-trivial size. It is recommended to
use [Globus](https://docs.alliancecan.ca/wiki/Transferring_data#Globus_transfer) to transfer this file to the Graham
cluster.

1. Install Globus on your server as suggested [here](https://www.globus.org/globus-connect-personal).
2. Login to the [Globus web portal](https://www.globus.org/app/transfer) using your HPC cluster credentials.
3. Choose your personal Globus endpoint as the source and the Graham Globus endpoint as the destination to transfer the
   Singularity instance file.
   See more at: https://docs.alliancecan.ca/wiki/Transferring_data#Globus_transfer

**MAKE SURE YOUR SINGULARITY CONTAINER IS AT THE FOLLOWING DIRECTORY: `$SCRATCH/netviz/readability-optimization/singularity/netviz-graham-v10.sif`**

**By now you should have completed setting up the virtual container. The following steps are for advanced usage.**

---

### 5. Request a Compute Node

> **Note: If you are using GraphOptima.py, you can ignore the rest of the steps for manually spawning a layout generator
node since GraphOptima.py will do it for you automatically.**

Request a compute node with a GPU and at least 16GB memory. Refer
to [Running jobs]( https://docs.alliancecan.ca/wiki/Running_jobs) for `salloc` command options.

```sh
salloc --ntasks=1 --mem=16G --gres=gpu:t4:1 --time=23:59:59 --account=username --job-name=layout_generator
```

### 6. Set Up the Virtual Environment

Navigate to the directory containing the transferred `.sif` Singularity instance file and set up the virtual environment
with the following command:

We assume the `.sif` file is the following
directory: `$SCRATCH/netviz/readability_optimization/singularity/netviz-graham-v10.sif`

```sh
module load apptainer
cd $SCRATCH/netviz/readability_optimization
singularity shell --nv -B $SCRATCH singularities/netviz-graham-v10.sif
```

The `--nv` option allows the virtual environment to communicate with the GPU, while `-B` projects the outside
directories into the virtual environment.

### 7. Activate the Environment: Run the following command to set up the path and activate the environment

```sh
export MPLCONFIGDIR=$SCRATCH
source /opt/conda/etc/profile.d/conda.sh
conda activate base
python cuGraph_to_pos_df.py
```

You can repeat this process as many times as you want to spawn multiple layout generators

### 8. See also 

[RAPIDS - CC Doc - Digital Research Alliance of Canada](https://docs.alliancecan.ca/wiki/RAPIDS)

[Singularity - CC Doc - Digital Research Alliance of Canada](https://docs.alliancecan.ca/wiki/Singularity)
