import sys
try:
    import torch
except Exception as e:
    print('IMPORT_ERROR', e)
    sys.exit(2)
print('PYTHON', sys.executable)
print('TORCH', getattr(torch, '__version__', 'unknown'))
print('CUDA_AVAILABLE', torch.cuda.is_available())
print('CUDA_VERSION', getattr(torch.version, 'cuda', None))
