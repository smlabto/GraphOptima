module load StdEnv/2020
module load python/3.11.2
virtualenv --no-download ENV
source ENV/bin/activate
pip install -r requirements.txt

