#!/bin/env bash
#
#SBATCH -p all                # partition (queue)
#SBATCH -c 12                      # number of cores
#SBATCH -t 200                # time (minutes)
#SBATCH -o /scratch/zmd/logs/mk_cell_map_%j.out        # STDOUT #add _%a to see each array job
#SBATCH -e /scratch/zmd/logs/mk_cell_map_%j.err        # STDERR #add _%a to see each array job
#SBATCH --contiguous #used to try and get cpu mem to be contigous
#SBATCH --mem 30000 #30 gbs

echo "In the directory: `pwd` "
echo "As the user: `whoami` "
echo "on host: `hostname` "

cat /proc/$$/status | grep Cpus_allowed_list

module load anacondapy/5.3.1
. activate lightsheet

echo "Array Index: $SLURM_ARRAY_TASK_ID"

python make_rawdata_cell_center_map.py ${SLURM_ARRAY_TASK_ID} 
