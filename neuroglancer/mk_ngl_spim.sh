#!/bin/env bash
#
#SBATCH -p all                # partition (queue)
#SBATCH -c 12                      # number of cores
#SBATCH -t 400                # time (minutes)
#SBATCH -o /scratch/zmd/logs/mk_ngl_spim_%j.out        # STDOUT #add _%a to see each array job
#SBATCH -e /scratch/zmd/logs/mk_ngl_spim_%j.err        # STDERR #add _%a to see each array job
#SBATCH --contiguous #used to try and get cpu mem to be contigous
#SBATCH --mem 80000 #80 gbs

echo "In the directory: `pwd` "
echo "As the user: `whoami` "
echo "on host: `hostname` "

cat /proc/$$/status | grep Cpus_allowed_list

module load anacondapy/5.3.1
. activate lightsheet

python make_precomputed_smartspim.py
