"""
PyInstaller Runtime Hook for onnxruntime
Disables CUDA providers to prevent nvcuda.dll loading errors

This runtime hook runs when the frozen application starts.
It configures onnxruntime to use only CPU providers and prevents
it from attempting to load CUDA DLLs that may not be available.

Author: Dead On The Inside / JosephsDeadish
"""

import os
import sys

# Disable CUDA for onnxruntime by setting environment variable BEFORE import
# This prevents onnxruntime from trying to load nvcuda.dll
os.environ['ORT_DISABLE_CUDA'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Also disable TensorRT and other GPU providers
os.environ['ORT_TENSORRT_UNAVAILABLE'] = '1'
