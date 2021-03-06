#!/bin/env bash
#
#SBATCH -p all                # partition (queue)
#SBATCH -c 1                      # number of cores
#SBATCH -t 200                # time (minutes)
#SBATCH -o /scratch/kellyms/logs/mkann_%a_%j.out        # STDOUT #add _%a to see each array job
#SBATCH -e /scratch/kellyms/logs/mkann_%a_%j.err        # STDERR #add _%a to see each array job
#SBATCH --contiguous #used to try and get cpu mem to be contigous
#SBATCH --mem 30000 #30 gbs

echo "In the directory: `pwd` "
echo "As the user: `whoami` "
echo "on host: `hostname` "

cat /proc/$$/status | grep Cpus_allowed_list

module load anacondapy/5.3.1
module load elastix/4.8
. activate lightsheet_py3

echo "Array Index: $SLURM_ARRAY_TASK_ID"

python 201903_kelly_transform_annotations_to_fullsize.py ${SLURM_ARRAY_TASK_ID}
