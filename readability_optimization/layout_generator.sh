cd $SCRATCH/netviz/readability_optimization/
export MPLCONFIGDIR=$SCRATCH
source /opt/conda/etc/profile.d/conda.sh
conda activate base

LAYOUT_GENERATOR=$(python -c "import json; print(json.load(open('config.json'))['optimizer']['LAYOUT_GENERATOR'])")

if [ "$LAYOUT_GENERATOR" = "cuGraph" ]; then
    python cuGraph_to_pos_df.py
elif [ "$LAYOUT_GENERATOR" = "graph-tool" ]; then
    python gt_to_pos_df.py
else
    echo "Invalid layout_generator value: $LAYOUT_GENERATOR"
    exit 1
fi
