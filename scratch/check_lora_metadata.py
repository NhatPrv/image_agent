import json
import struct
from pathlib import Path

lora_path = Path(r"C:\mydata\selfproject\image_agent\models\loras\Lalisamanoban.safetensors")

if not lora_path.exists():
    print(f"File not found: {lora_path}")
    exit(1)

with open(lora_path, "rb") as f:
    # Read header size (8 bytes, little endian unsigned long long)
    header_size_bytes = f.read(8)
    if len(header_size_bytes) < 8:
        print("Invalid safetensors file: too short")
        exit(1)
    header_size = struct.unpack("<Q", header_size_bytes)[0]
    
    # Read header
    header_bytes = f.read(header_size)
    if len(header_bytes) < header_size:
        print("Invalid safetensors file: header truncated")
        exit(1)
    
    header = json.loads(header_bytes.decode("utf-8"))
    
    # Metadata is stored in "__metadata__" key
    metadata = header.get("__metadata__", {})
    print("=== METADATA ===")
    print(json.dumps(metadata, indent=2))
    
    # Look for keys to determine model architecture (e.g. presence of unet vs transformer keys)
    keys = list(header.keys())
    print("\n=== LAYER KEYS INFO ===")
    print(f"Total keys: {len(keys)}")
    
    sdxl_indicators = ["lora_unet_down_blocks", "double_blocks", "single_blocks"]
    sd15_indicators = ["lora_te_text_model", "lora_unet_up_blocks"]
    
    is_sdxl = any(any(ind in k for ind in sdxl_indicators) for k in keys)
    is_sd15 = any("lora_unet_input_blocks" in k for k in keys)
    is_flux = any("double_blocks" in k or "single_blocks" in k for k in keys)
    
    print(f"Detected potential architectures:")
    print(f" - SDXL: {is_sdxl}")
    print(f" - SD 1.5: {is_sd15}")
    print(f" - Flux: {is_flux}")
