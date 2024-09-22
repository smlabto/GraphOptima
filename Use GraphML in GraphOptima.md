# Use GraphML in GraphOptima

In this document, you will find: 
1. how to use your own `graphml` as the input for the GraphOptima.
2. how to generate sample graphs similar to the default price network using `graph-tool`.

> **Note:** To use your own graph, ensure that the graph has no parallel edges or self-loops. If the graph has parallel edges or self-loops, use the `graph_cleaning.ipynb` notebook to clean the graph.
> After that, it is recommended to reformat the cleared csv edgelist into a tsv (tab-separated values) file, since GraphOptima has been through tested with tsv files.

## Prerequisites
- Before proceeding, ensure the GraphOptima has been installed (refer to `README.md`).

## Use Custom GraphML in GraphOptima

1. **Move your GraphML input graph to the `input_graphs` folder**

   Make sure the GraphML file is located under the `$SCRATCH/netviz/readability_optimization/input_graphs/graph_file_name.graphml`. Change `GRAPHML_FILE` field of the `readability_optimization/config.json` to `input_graphs/graph_file_name.graphml`


2. **Remove redundant graph properties (Optional)**
   
   A large GraphML file may slow down the framework and crush the layout generator. To avoid this, remove large text properties and those that are not used during the layout calculation. Check out `readability_optimization/input_graphs/graph_cleaning.ipynb`, which shows a example of using `graph-tool` to remove all the vertex and edge properties, parallel edges, and self-loops.


3. **Filter graph by GraphTrimmer (Optional)**

   It the field of social network analysis, it is common to perform some pre-filtering of the graph to only focus on the interested relationships. Simpler graph by nature is easier to optimize and read. We provide a convent tool `GraphTrimmer` to filter the graph by the degree of the nodes. The `GraphTrimmer` is a Python script that can be found in the `readability_optimization` folder. The script will remove the nodes with degree less than the threshold. To use the `GraphTrimmer`, run the following command:

   ```bash
   python GraphTrimmer.py --input_graph input_graphs/graph_file_name.graphml --output_graph input_graphs/graph_file_name_trimmed.graphml --threshold 10 --filter_type reciprocal
   ```
   
   `GraphTrimmer` provides four modes of filtering: in, out, total and reciprocal. 
    - `in`: filter the nodes with in-degree (a<-b) less than the threshold.
    - `out`: filter the nodes with out-degree (a->b) less than the threshold.
    - `total`: filter the nodes with total degree (in + out) less than the threshold.
    - `reciprocal`: filter the nodes with reciprocal (mutual, meaning a<->b) degree less than the threshold.
    
    > NOTE: `graph-tool` is not available under Windows. To run the `GraphTrimmer`, it is recommended to use either the Singularity environment outlined in the `README`, or to use the following docker environment (since singularity is not available on Windows): https://hub.docker.com/repository/docker/0xc00005/netviz-graham-v10/general 

## How to generator sample graphs

1. **Enter the Singularity Environment**

    Navigate to the appropriate directory and start the Singularity environment with the following command:

    ```bash
    module load singularity
    cd $SCRATCH 
    singularity shell --nv -B $SCRATCH $SCRATCH/netviz/readability_optimization/singularity/netviz-graham-v10.sif
    ```

2. **Init the Singularity Container**

    Within the Singularity environment, set up the PATH variable and enable the RAPIDS environment with the following command:

    ```bash
    export MPLCONFIGDIR=$SCRATCH
    source /opt/conda/etc/profile.d/conda.sh
    conda activate base
    ```

3. **Navigate to `input_graphs` Folder**

    Proceed to the sample graph folder. 

    ```bash
    cd input_graphs
    ```

4. **Run graph-to-network Generation Script**

    Execute the Python script `generate_networks_with_gt.py `. This generates various network types such as Price Network, Complete Graph, Block Model, and others.


5. **Run `csv2tsv.py` Script**

    After the `graph_tool_network_generation.py ` script finishes running, execute `csv2tsv.py`. This script first uses an open-source script `graphml2csv.py` provided by the Amazon Graph Science Team, `graphml2csv.py`, to convert GraphML files to CSV format. Then, it converts these CSV files to TSP.

    Upon completion, each GraphML network file hwill yield three different CSV/TSP files with distinct prefixes. The one used in our paper is `fixed_price_10000_nodes_edges.csv` and `price_10000.graphml`.
   

6. **Validate the Outputs**

     Ensure that the graph with format "fixed_<graph_name>-edge.csv" is present in the `sample_graphs` directory. This file will be used as input for the GraphOptima framework.