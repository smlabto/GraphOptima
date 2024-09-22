# Use the specified base image from Docker Hub
FROM rapidsai/notebooks:24.04-cuda12.0-py3.11

# Set up the environment in the image
USER root
RUN apt-get update && apt-get install -y git

# Initialize conda environment
RUN /opt/conda/bin/conda init bash

# Install packages in the conda environment
RUN bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate base && \
    conda config --set remote_read_timeout_secs 600.0 && \
    conda install --solver=libmamba pytorch torchvision torchaudio pytorch-cuda=12.1 jupyterlab ipython graph-tool pymoo filelock pyyaml pygraphviz -c pytorch -c nvidia -c conda-forge -q -y"

# Labels for metadata
LABEL Version="v10.2.0"
LABEL Author="maxjingweizhang@ryerson.ca"
LABEL Description="An integrated virtual environment for GraphOptima: Framework for Optimizing Graph Layout and Readability on Compute Canada's Graham cluster"