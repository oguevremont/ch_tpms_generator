#!/bin/bash
#SBATCH --account=rrg-fede1988
#SBATCH --ntasks-per-node=1 #number of parallel tasks (as in mpirun -np X)
#SBATCH --nodes=1 #number of whole nodes used (each with up to 40 tasks-per-node)
#SBATCH --time=0:15:00 #maximum time for the simulation (hh:mm:ss)
#SBATCH --job-name=launch_all
#SBATCH --mail-type=END #email preferences
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=guevremont.o@gmail.com

source $HOME/.dealii
module load CCEnv #if on Niagara
module load StdEnv/2023
module load vtk/9.3.0
module load python/3.11.5
module load scipy-stack/2023b

source ENVGEN_POREUX/bin/activate

python main.py

deactivate
