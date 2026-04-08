import os
try:
    import rasterio
    import numpy as np
    from PIL import Image
except ImportError:
    rasterio = None
    np = None
    Image = None

import logging

def export_heightmap(tif_path: str, output_path: str):
    """
    Converts a 32-bit float GeoTIFF to a 16-bit PNG heightmap for Unreal Engine.
    Unreal expects 16-bit Grayscale for landscapes.
    """
    if not rasterio or not np or not Image:
        print("Missing required libraries: rasterio, numpy, pillow")
        return

    if not os.path.exists(tif_path):
        print(f"Input TIF not found: {tif_path}")
        return

    with rasterio.open(tif_path) as src:
        data = src.read(1)
        
        # Normalize to 16-bit range (0-65535)
        # We find the min/max of the data
        d_min = data.min()
        d_max = data.max()
        
        print(f"Original elevation range: {d_min}m to {d_max}m")
        
        # Scale float -32768 to 32767 usually doesn't apply to pure elevation
        # Unreal uses 0-65535, where 32768 is roughly sea level if centered
        # For simplicity, we normalize the local range to the full 16-bit space
        normalized = (data - d_min) / (d_max - d_min) * 65535
        uint16_data = normalized.astype(np.uint16)
        
        # Convert to Image and save
        img = Image.fromarray(uint16_data, mode='I;16')
        img.save(output_path)
        print(f"Heightmap exported successfully: {output_path}")
        
if __name__ == "__main__":
    # Test export for Antietam if exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Using the specific file found in data/terrain
    tif = os.path.join(base_dir, "..", "..", "data", "terrain", "a1b2c3d4-1111-4444-aaaa-000000000001_elevation.tif")
    out = os.path.join(base_dir, "..", "..", "data", "terrain", "ue5_heightmap.png")
    export_heightmap(tif, out)
