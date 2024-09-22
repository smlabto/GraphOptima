cd $SCRATCH/netviz/readability_optimization/

# Check if the ENV directory exists
if [ ! -d "ENV" ]; then
  echo -e "\n\n\n\nENV directory does not exist. Creating it by running build_venv.sh...\n\n\n\n"
  # Run the build_venv.sh script
  bash build_venv.sh

  # Check if the script ran successfully
  if [ $? -eq 0 ]; then
    echo -e "\n\n\n\nENV directory created successfully.\n\n\n\n"
  else
    echo -e "\n\n\n\nFailed to create ENV directory. Check the build_venv.sh script for errors.\n\n\n\n"
    exit 1
  fi
else
  echo -e "\n\n\n\nENV directory already exists.\n\n\n\n"
fi

# Check if glam/build/glam exists
if [ ! -f "glam/build/glam" ]; then
  echo -e "\n\n\n\nglam/build/glam does not exist. Running build_glam.sh...\n\n\n\n"
  # Run the build_glam.sh script
  bash build_glam.sh

  # Check if the script ran successfully
  if [ $? -eq 0 ]; then
    echo -e "\n\n\n\nglam/build/glam created successfully.\n\n\n\n"
  else
    echo -e "\n\n\n\nFailed to create glam/build/glam. Check the build_glam.sh script for errors.\n\n\n\n"
    exit 1
  fi
else
  echo -e "\n\n\n\nglam/build/glam already exists.\n\n\n\n"
fi

# Check if singularity/netviz-graham-v10.sif exists
if [ ! -f "singularity/netviz-graham-v10.sif" ]; then
  echo -e "\n\n\n\nsingularity/netviz-graham-v10.sif does not exist."
  echo -e "Downloading the container from the Google Drive..."
  bash build_singularity.sh
  echo "You can also build a new container following the 'Compute Canada's Graham Cluster Using Singularity.md' instructions."
  echo -e "Installation complete.\n\n\n\n"
else
  echo -e "\n\n\n\nsingularity/netviz-graham-v10.sif already exists."
  echo -e "Installation complete.\n\n\n\n"
fi
