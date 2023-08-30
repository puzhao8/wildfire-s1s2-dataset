#!/bin/bash
#SBATCH --mem-per-cpu 20000M
#SBATCH --cpus-per-task 8
#SBATCH --gres=gpu:1
#SBATCH --mem=0
#SBATCH -t 7-00:00:00
#SBATCH --job-name data-prg
#SBATCH --output /home/v/i/vishaln/run_logs/data-down.out
#SBATCH --error /home/v/i/vishaln/run_logs/data-down-err.out

echo "start"
echo "Starting job ${SLURM_JOB_ID} on ${SLURMD_NODENAME}"
echo
nvidia-smi
. /geoinfo_vol1/puzhao/miniforge3/etc/profile.d/conda.sh

conda activate pytorch-lit

unset KUBERNETES_PORT
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9
export NCCL_DEBUG=INFO
export PYTHONFAULTHANDLER=1
PYTHONUNBUFFERED=1

python3 /home/v/i/vishaln/code/wildfire-s1s2-dataset/main_s1s2_prg.py \