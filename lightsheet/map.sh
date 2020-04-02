#!/bin/env bash
#
#SBATCH -p all                # partition (queue)
#SBATCH -c 6                      # number of cores
#SBATCH -t 60                 # time (minutes)
#SBATCH -o /scratch/zmd/logs/map_%j.out        # STDOUT #add _%a to see each array job
#SBATCH -e /scratch/zmd/logs/map_%j.err        # STDERR #add _%a to see each array job
#SBATCH --contiguous #used to try and get cpu mem to be contigous
#SBATCH --mem 80000 #80gbs

echo "In the directory: `pwd` "
echo "As the user: `whoami` "
echo "on host: `hostname` "

cat /proc/$$/status | grep Cpus_allowed_list

module load anacondapy/5.3.1
. activate lightsheet

python check_cell_center_mapping.py 
