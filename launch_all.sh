#!/bin/bash
#SBATCH --account=rrg-fede1988
#SBATCH --ntasks-per-node=1 #number of parallel tasks (as in mpirun -np X)
#SBATCH --nodes=1 #number of whole nodes used (each with up to 40 tasks-per-node)
#SBATCH --time=0:10:00 #maximum time for the simulation (hh:mm:ss)
#SBATCH --job-name=launch_all
#SBATCH --mail-type=END #email preferences
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=guevremont.o@gmail.com

module load python/3.11.5
virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip

pip install --no-index -r $HOME/requirements.txt
source $HOME/.dealii

python main.py 

deactivate
