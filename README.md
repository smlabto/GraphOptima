# GraphOptima: Framework for Optimizing Graph Layout and Readability

![GraphOptima's Result](https://raw.githubusercontent.com/0xC000005/image-hosting/master/GraphOptima_results_sample1.png)

Welcome to GraphOptima, a framework for paralleled multi-objective optimization of graph layouts. Given a set of
readability metrics, the framework aims to produce layouts that are optimum given different priority of each
readability metrics.


The framework supports the optimization of parameters for the `cugraph.forceAtlas2` layout. To optimize other layouts,
one can create a simple Python script that takes a layout parameter and outputs a dataframe of all vertices positions,
as detailed in the FaQ.

The framework optimizes for layout `crosslessness` (number of edge crossings), `normalized_edge_length_variance`,
and `min_angle` (average angles between edges), with metrics measured using the `GLAM` library. Similar to the layout
generation process, the modular design of the framework allows users to add more readability metrics or even use
readability metrics from other libraries. For instructions on how to do this, please refer to the FaQ.

GraphOptima supports two modes of operation:

1. **Automatic Mode**: In this mode, users need it only execute the `GraphOptima.py` master program. It automatically
   configures layout generators and evaluators based on a predefined task specified in the `config.json`. **Note**: This
   mode relies on a sbatch file compatible with Compute
   Canada's [Slurm Work Manager](https://slurm.schedmd.com/documentation.html), which may not be suitable for all HPC
   clusters.
2. **Manual Mode**: This mode requires users to manually initiate multiple layout generators, evaluators, and the
   optimizer. It offers real-time output into the workings of each module.

## Setup

We strongly recommend setting up GraphOptima on top of a High-Performance Computing (HPC) cluster with GPU for maximum
performance.
Since the framework relies on file synchronization to pass information between nodes, the cluster should have access to
a shared file system such as [Lustre](https://docs.alliancecan.ca/wiki/Tuning_Lustre).

Setting up GraphOptima involves the following steps:

- **Download the GraphOptima to an HPC:** Download the GraphOptima
   framework code from our GitHub repository to an HPC. In our
   tutorial, we use [Graham](https://docs.alliancecan.ca/wiki/Graham) from the Digital Research Alliance of Canada (formerly, Compute Canada). We recommend moving it to the `$SCRATCH` directory for the maximum performance.

- **Automatic Setup:** run `bash netviz/readability_optimization/install.sh`

- **Manual Setup:** 
  - **Set Up [Apptainer](https://docs.alliancecan.ca/wiki/Apptainer) Virtual Container:** For detailed steps, refer
     to [Setting up cuGraph layout generators on Compute Canada's Graham Cluster Using Singularity.md](https://github.com/SocialMediaLab/netviz/blob/master/Setting%20up%20cuGraph%20layout%20generators%20on%20Compute%20Canada's%20Graham%20Cluster%20Using%20Singularity.md) and follow steps
     1–4.
      1. **Note:** the `Singularity` has now been renamed to `Apptainer`, and the steps in the tutorial works for both
         Singularity
         and Apptainer.

  -  **Create a python virtual environment**: Create a virtual environment `ENV` under the `readability_optimization`
     directory
     using the `requirements.txt`. On Graham, you can do the following:
      1. `module load StdEnv/2020`
      2. `module load python/3.11.2`
      3. `cd readability_optimization`
      4. `virtualenv --no-download ENV`
      5. `source ENV/bin/activate`
      6. `pip install -r requirements.txt`
   
  >   NOTE: make sure after the env is created, it is on `$SCRATCH/netviz/readability_optimization/ENV` directory.

  -  **Generate Sample Graphs (Optional):** By default, the GraphOptima will optimize a example price network stored under the `input_graph` folder as `.graphml`. However, if you want to generate more graphs After setting up the singularity instance, generate test graph for test optimizations. 
     Following instructions in [Use GraphML in GraphOptima.md](https://github.com/SocialMediaLab/netviz/blob/master/Sample%20Graph%20Generation%20Tutorial.md).
      1. For optimizing you own graphs, use `input_graphs/graph_cleaning.ipynb` to pre-process the graph. Store the
         cleaned `graphml` file in the `input_graphs` directory.

  - **Set Up GLAM Layout Evaluator:** Finally, set up the GLAM layout evaluator. See steps 1–4
     in [Setting up GLAM layout evaluators on Compute Canada.md](https://github.com/SocialMediaLab/netviz/blob/master/Setting%20up%20GLAM%20layout%20evaluators%20on%20Compute%20Canada.md). After the installation, ensure that the `GLAM` executable
      is in `$SCRATCH/netviz/readability_optimization/glam/build/glam`

After these steps, the framework setup is complete and ready for use.

## Usage

### Automatic Mode

![](https://raw.githubusercontent.com/0xC000005/image-hosting/master/202406041132405.gif)

Under the automatic mode, the Framework will automatically spawn layout generators, evaluators, and optimizer based on
the config file, and revive any killed node until the optimization is complete. The user won't be able to see the output
from the layout generators and evaluators under this mode.

For automatic mode, follow these steps:

1. **Configure JSON File:** Configure the `config.json` file following the instructions
   in [How to set up the config file.md](https://github.com/SocialMediaLab/netviz/blob/master/Setting%20up%20GLAM%20layout%20evaluators%20on%20Compute%20Canada.md).
2. **Run the following commands:**
   1. `cd $SCRATCH/netviz/readability_optimization`
   2. `bash GraphOptima.sh`
   - > NOTE: the GraphOptima.py needs to be running until the optimization is complete. Thus, it is strongly recommended
     to hang it on a `screen` session.
   
   This script communicates with the Slurm Queue task manager to automatically allocate the designated number of
   layout evaluators, layout generators, and optimizers based on the config file. 
   It will also automatically respawn any computing nodes using `SBATCH`. The script needs to remain open during the 
   entire optimization process. Thus, it is recommended to hang it on a `screen` session. 

   > It is strongly recommended to enable email notification when submitting jobs through `SBATCH`, so when the 
   submission failed, one can roll back and check the error before the framework attempts to resubmit the job. To enable 
   the email notification, add the following lines to the top of every `SBATCH` script:
   > - `#SBATCH --mail-user=example@mail.com`
   > - `#SBATCH --mail-type=begin #email when job starts`
   > - `#SBATCH --mail-type=end #email when job ends`
   > - `#SBATCH --mail-type=ALL`

### Manual Mode
![](https://raw.githubusercontent.com/0xC000005/image-hosting/master/GraphOptima1.gif)
![](https://raw.githubusercontent.com/0xC000005/image-hosting/master/GraphOptima2.gif)

Under the manual mode, the user will need to manually spawn multiple screen sessions to hang on the layout generators,
evaluators and the optimizer. The user will be able to see the real time output from each module.

> NOTE: the manual mode is still going to read the config file for specifying input graph etc. However, it won't call
> the sbatch file to spawn the layout generators and evaluators automatically.

| Module                          | Environment             | GPU Requirement | RAM Requirement | Container/Virtual Environment | Description                                                                 |
|---------------------------------|-------------------------|-----------------|-----------------|-------------------------------|-----------------------------------------------------------------------------|
| Optimizer                       | Login or computing node | No              | -               | Singularity                   | Finds the best set of parameters for the most readable layout               |
| Layout Generator                | Computing node          | Yes (≥Tesla T4) | ≥ 16 GB         | Singularity                   | Reads parameters set by the optimizer and generates a layout accordingly    |
| Layout Evaluator                | Computing node          | Yes             | ≥ 16 GB         | Python venv                   | Calculates readability from the layout generated by the layout generator    |
| Database Viewer (optional)      | Computing node          | No              | ≥ 16 GB         | Python venv                   | Allows users to view the database connected to the optimizer in real-time   |
| External API Monitor (optional) | Login or computing node | No              | -               | Python venv                   | Enables framework communication via the internet, e.g., email notifications |


For manual mode, follow these steps:

> **NOTE:** These modules have to run in parallel. It is recommended to use `screen` to manage multiple sessions.

1. **Spawn Layout Generators**:
   1. `module load apptainer`
   2. `salloc --ntasks=1 --mem=16G --gres=gpu:t4:1 --time=3:59:59 --account=username --job-name=layout_generator`
   2. `module load apptainer`
   3. `cd $SCRATCH/netviz/readability_optimization`
   4. `singularity shell --nv -B /scratch singularity/netviz-graham-v10.sif`
   5. `bash layout_generator.sh`

2. **Spawn Layout Evaluators**:
   1. `salloc --ntasks=1 --mem=16G --gres=gpu:t4:1 --time=3:59:59 --account=username --job-name=layout_evaluator`
   2. `module load apptainer`
   3. `cd $SCRATCH/netviz/readability_optimization`
   4. `bash layout_evaluator.sh`

3. **Set Up the Optimizer Node**:
   1. `salloc --ntasks=1 --mem=16G --time=3:59:59 --account=username --job-name=optimizer`
   2. `module load apptainer`
   3. `cd $SCRATCH/netviz/readability_optimization`
   4. `singularity shell --nv -B /scratch singularity/netviz-graham-v10.sif`
   5. `bash optimizer.sh`

4. **Set Up the Database Viewer (Optional)**:
   1. `salloc --ntasks=1 --mem=16G --time=3:59:59 --account=username --job-name=database_viewer`
   2. `cd $SCRATCH/netviz/readability_optimization`
   3. `source ENV/bin/activate`
   4. `python optimization_database.py`

5. **Set Up the External API Monitor (Optional)**:
    1. `cd $SCRATCH/netviz/readability_optimization`
    2. `source ENV/bin/activate`
    3. `python external_api.py`

## Interpretation of Results

To visualize the result after optimization, as shown in the image at the beginning of this README, follow these steps:

- After running the optimization, run `make_mat.py` with all `.db` files generated by the optimizer stored in the `/database`
directory. Then move the `.mat` file to the `visulizations` folder. 

- After the `.mat` file is generated, follows [Collecting, Extracting, and Interpreting Optimization Results using Python and MATLAB.md](https://github.com/SocialMediaLab/netviz/blob/master/Collecting%2C%20Extracting%2C%20and%20Interpreting%20Optimization%20Results%20using%20Python%20and%20MATLAB.md) to visualize the
multi-objective optimization results as Pareto fronts and examine trade-offs between each readability metric.

- To visualize a given graph using [RAPIDS cuGraph](https://docs.rapids.ai/api/cugraph/stable/) based on the selected
layout parameters, follow instructions outlined
in [Using cuGraph, Singularity, and Jupyter Notebook to Reproduce and Visualize Layouts.md](https://github.com/SocialMediaLab/netviz/blob/master/Using%20cuGraph%2C%20Singularity%2C%20and%20Jupyter%20Notebook%20to%20Reproduce%20and%20Visualize%20Layouts.md).

## Architecture Overview
![](https://raw.githubusercontent.com/0xC000005/image-hosting/master/330566790-93f43880-5c1b-443c-b182-a1f943ea7571.png)


### Core Modules

- **Optimizer Module**: Utilizes an evolutionary algorithm to explore and propose optimal combinations of layout
  parameters. It applies multi-objective optimization to balance different readability metrics, like edge crossings and
  angle uniformity, optimizing the overall layout based on a weighted readability score.

- **Layout Generator Module**: Receives parameters from the Optimizer and generates graph layouts. This module is built
  for parallel processing across multiple compute nodes, enabling the rapid creation of layouts using algorithms such as
  ForceAtlas2 from the cuGraph library. It's designed to handle an extensive range of layout algorithms and parameters,
  ensuring flexibility and speed.

- **Layout Evaluator Module**: Assesses the generated layouts using the GLAM package for readability metrics, including
  crosslessness, minimum angle, and edge length variance. This module supports the integration of additional or custom
  readability metrics, making it adaptable to various evaluation needs.

### Supporting Modules

- **High-Performance Computing (HPC) Environment**: GraphOptima leverages HPC resources for scalable and efficient
  optimization, using distributed computing nodes for both layout generation and evaluation.

- **Task Distributor**: Facilitates communication between different modules using a shared filesystem, ensuring seamless
  operation and data exchange within the distributed environment.

- **External API Monitor Module**: Monitors the runtime of optimization jobs and manages compute resources to ensure
  continuous operation, including the ability to restart or spawn new compute nodes as needed.

- **Database Manager**: Stores and manages the results of optimization runs, including layout parameters and readability
  metrics, to prevent redundant testing and enhance the efficiency of the optimization process.

- **Interactive Visualizer**: Provides a graphical interface for exploring optimization results through a 3D scatter
  plot of the Pareto front, allowing users to visually compare and select optimal layout solutions based on their
  preferences.

## FaQ

### 1. How to change the layout used in the layout generator?

1. change the `layout_generator.sh` to add a new layout option with its python wrapper
2. add the python wrapper. The wrapper should be similar to `cuGraph_to_pos_df.py` and `gt_to_pos_df.py`: take a list of
   layout params and output a dataframe with x, y position of each node.

### 2. How to change the layout evaluator?

Currently, the layout evaluator is using GLAM. To change it to another backend or to incorporate other metrics, one can
change the `dot_to_readability_score.py`.
After the graph layout is generated, a corresponding dot file is generated. The `dot_to_readability_score.py` reads the
dot file and outputs a readability score by running subprocess calling GLAM. One just need to add their own readability
evaluation method here as a subprocess to incorporate other metrics.
