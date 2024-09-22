# Using cuGraph, Singularity, and Jupyter Notebook to Reproduce and Visualize Layouts

In this tutorial, we will cover how to use cuGraph, Singularity, and Jupyter Notebook to easily reproduce and visualize network layouts.

> Note: for steps 1–3, see `Setting up cuGraph layout generators on Compute Canada's Graham Cluster Using Singularity.md` for more details.

1. **Install Singularity:** You first need to install Singularity on your system and open an interactive shell with RAPIDS virtual environment enabled. 
2. **Enter the Singularity environment:** After Singularity is installed, open it and enter the virtual environment.
3. **Activate the Environment:** Inside the Singularity environment, you'll need to activate the 'RAPIDS' virtual environment.

> Note: for steps 4–7, see [RAPIDS - CC Doc (alliancecan.ca)](https://docs.alliancecan.ca/wiki/RAPIDS) for more details.

4. **Run Jupyter Notebook:** Now you need to execute the Jupyter Notebook command.
5. **Establish SSH Tunnel:** You need to establish an SSH tunnel to your computing node.
6. **Navigate to the Project Directory:** Once you've SSH'd into your node, navigate to the project's directory and open the `cuGraph_graph-tool_plot.ipynb` Jupyter notebook.
7. **Run the Notebook:** Run all the blocks in the notebook up until the last two. You can then customize the parameters and run the remaining blocks.

In the notebook, we demonstrate two ways of visualizing a network:

- **Network Visualization:** The first method visualizes the network as a traditional graph with nodes and edges using `graph_tool` (it works well with small-mid size graphs).

- **Heat Chart:** The second method visualizes the network as a heat chart. This method is especially useful when visualizing large networks, as rendering nodes and edges traditionally can be time-consuming, while generating a heat chart is faster.

Note: If you want to visualize networks other than the `Price_10000` network, you need to change the GraphML and CSV files loaded at the beginning of the Jupyter notebook. See the `Simple Network Generation.md` tutorial for more information on where to find additional networks and the required formats.
