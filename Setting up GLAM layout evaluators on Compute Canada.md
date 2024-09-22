# Setting up GLAM layout evaluators on Compute Canada

The framework uses the Graph Layout Assessment Metrics ([GLAM](https://github.com/kwonoh/glam)) program to measure graph readability metrics based on a given graph. GLAM provides several readability metrics, like 'crosslessness', which measures the number of edge crossings. We've created a wrapper around GLAM to handle file input/output and ensure seamless integration with our framework.

To use GLAM, you need to install it first on the HPC. Here we demonstrate how to install GLAM on the Graham cluster of the Digital Research Alliance of Canada. 

>Note: the GLAM only needs to be installed once. Since the filesystem is shared, there will be a copy of installed GLAM in the same directory across all computing nodes.

### Step 1: Load Required Modules

```bash
module load StdEnv/2020 gcc/9.3.0 boost/1.72.0 cgal/4.14.3 tbb/2020.2 
```

>NOTE: Do not upgrade any loaded modules, even if suggested by the output of the `module` output. Upgrading can cause `intel/2021.2.0` to become a dependency and confuse the `OpenCl` module that comes with NVIDIA's driver preinstalled on the Graham cluster.

### Step 2: Request a Compute Node with GPU (Optional)

**Note:** This step is only needed if you want to test run the GLAM afterwards.

```bash
nvidia-smi
```
If the command outputs `No devices were found`, or if the CUDA version is not displayed, we need to request a compute node with a graphics card on the Graham cluster:

```bash
salloc --ntasks=1 --mem=16G --gres=gpu:p100:1 --time=8:0:0 --account=username
```

### Step 3: Download and Compile GLAM

```bash
git clone https://github.com/kwonoh/glam.git
cd glam
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release; make
```

If `cmake` complains about not finding the `boost::thread` module, use the following forked [glam repo](https://github.com/0xC000005/glam) with a modified 'cmakefile' instead.

### Step 4: Test Run (Optional)

First go to the directory of the compiled glam executable. 
```bash
cd glam/build/
```

Run GLAM with a single file and metric:

```bash
./glam ../data/karate.dot -m crosslessness
```

Or with multiple files and metrics:

```bash
./glam ../data/karate.dot ../data/power.json -m crosslessness shape_gabriel
```

For help, use the '--help' option:

```bash
./glam --help
```

### Step 5: Request a computing node and run the Layout Evaluator

>**Note: If you are using GraphOptima.py, you can ignore the rest of the steps of manually spawning a layout evaluator node since GraphOptima.py will do it for you.**

Request a computing node with GPU installed and at least 16GB of memory:

```bash
salloc --ntasks=1 --mem=16G --gres=gpu:t4:1 --time=3:59:59 --account=username --job-name=layout_evaluator
cd $SCRATCH/netviz/readability_optimization
bash layout_evaluator.sh
```

The command listed above can be executed at multiple screens to spawn several layout evaluators to speed up the optimization process.
