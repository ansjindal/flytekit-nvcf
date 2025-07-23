#!/usr/bin/env python

import logging
import time
import numpy as np
import torch
import ray

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@ray.remote(num_gpus=1)
def multiply_matrices_on_gpu_pytorch(matrix_a, matrix_b):
    """
    A Ray remote function that multiplies two matrices on a GPU using PyTorch.
    Ray automatically passes the actual data, not the ObjectRefs.
    """
    logging.info("Executing on a worker with a GPU using PyTorch.")

    # The arguments `matrix_a` and `matrix_b` are already the NumPy arrays.
    # The unnecessary ray.get() calls have been removed.

    # Check if a CUDA-enabled GPU is available for PyTorch
    if not torch.cuda.is_available():
        error_msg = "PyTorch cannot find a CUDA-enabled GPU. This task requires a GPU worker."
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    # Set the device to the first available CUDA device.
    device = torch.device("cuda:0")
    logging.info(f"Using device: {torch.cuda.get_device_name(device)}")

    # Convert the NumPy arrays to PyTorch tensors and move them to the GPU.
    tensor_a = torch.from_numpy(matrix_a).to(device)
    tensor_b = torch.from_numpy(matrix_b).to(device)

    # Perform the matrix multiplication on the GPU.
    result_tensor = tensor_a @ tensor_b

    # To return the result, it must be moved back to the CPU and converted to a NumPy array.
    result_numpy = result_tensor.cpu().numpy()
    logging.info("Matrix multiplication on GPU complete.")

    return result_numpy

def main():
    """
    Main function to demonstrate GPU matrix multiplication with PyTorch and Ray.
    """
    # This will connect to the existing Ray cluster started by the job submission.
    ray.init(address='auto')

    matrix_size = 2048

    logging.info(f"Creating two {matrix_size}x{matrix_size} matrices on the CPU.")
    cpu_matrix_a = np.random.rand(matrix_size, matrix_size).astype(np.float32)
    cpu_matrix_b = np.random.rand(matrix_size, matrix_size).astype(np.float32)

    # Use ray.put() to store large objects in the cluster's distributed object store.
    logging.info("Placing large matrices into the Ray object store.")
    matrix_a_ref = ray.put(cpu_matrix_a)
    matrix_b_ref = ray.put(cpu_matrix_b)

    logging.info("Submitting the PyTorch matrix multiplication task to Ray.")
    result_ref = multiply_matrices_on_gpu_pytorch.remote(matrix_a_ref, matrix_b_ref)

    # Block and wait for the result.
    start_time = time.time()
    result_matrix = ray.get(result_ref)
    end_time = time.time()

    logging.info(f"Successfully retrieved the result.")
    logging.info(f"PyTorch matrix multiplication on GPU took {end_time - start_time:.4f} seconds.")
    logging.info(f"Result matrix shape: {result_matrix.shape}")

    ray.shutdown()

if __name__ == "__main__":
    main()
