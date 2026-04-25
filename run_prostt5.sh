#!/bin/bash
#SBATCH --job-name=prostt5_retrieval
#SBATCH --output=logs/prostt5_%j.out
#SBATCH --error=logs/prostt5_%j.err
#SBATCH --time=12:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Job started: $(date)"
echo "Running on node: $(hostname)"
echo "GPU info:"
nvidia-smi

# Load required modules (adjust to what's available on Engaging)
module load python/3.12 2>/dev/null || module load python3 2>/dev/null || true
module load cuda 2>/dev/null || true

# Activate the virtual environment
source /path/to/your/SAPER/.venv/bin/activate

# Navigate to script directory
cd /path/to/your/SAPER/structural_retrieval/src

echo "Python: $(which python)"
echo "PyTorch CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')"

python prostt5_retrieval.py

echo "Job finished: $(date)"
