import os
import httpx
try:
    import rasterio
    from rasterio.merge import merge
except ImportError:
    rasterio = None
import numpy as np
import logging
try:
    import pyproj
except ImportError:
    pyproj = None

class TerrainData:
    def __init__(self, battle_id: str, bounds: dict):
        self.battle_id = battle_id
        self.bounds = bounds
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "terrain")
        self.tif_path = os.path.join(self.cache_dir, f"{self.battle_id}_elevation.tif")
        self.elevation_data = None
        self.transform = None
        self.proj_transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True) if pyproj else None
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    async def _download_srtm(self):
        """Downloads Mapzen GeoTIFF tiles from AWS S3 and stitches them."""
        import mercantile
        from rasterio.merge import merge
        import io

        zoom = 12
        tiles = list(mercantile.tiles(
            self.bounds["west"], self.bounds["south"],
            self.bounds["east"], self.bounds["north"],
            zoom
        ))
        
        logging.info(f"Downloading {len(tiles)} Mapzen tiles at zoom {zoom} for battle {self.battle_id}...")
        
        temp_files = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for tile in tiles:
                    url = f"https://s3.amazonaws.com/elevation-tiles-prod/geotiff/{tile.z}/{tile.x}/{tile.y}.tif"
                    response = await client.get(url)
                    if response.status_code == 200:
                        temp_path = os.path.join(self.cache_dir, f"temp_{tile.z}_{tile.x}_{tile.y}.tif")
                        with open(temp_path, 'wb') as f:
                            f.write(response.content)
                        temp_files.append(temp_path)
                    else:
                        logging.warning(f"Failed to fetch tile {tile.z}/{tile.x}/{tile.y}: {response.status_code}")
                        
            if not temp_files:
                logging.error("Failed to download any terrain tiles.")
                return

            # Stitch via rasterio
            src_files_to_mosaic = []
            for fp in temp_files:
                src = rasterio.open(fp)
                src_files_to_mosaic.append(src)

            mosaic, out_trans = merge(src_files_to_mosaic)
            
            # Update metadata
            out_meta = src_files_to_mosaic[0].meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans
            })
            
            with rasterio.open(self.tif_path, "w", **out_meta) as dest:
                dest.write(mosaic)
                
            logging.info(f"Successfully cached stitched GeoTIFF at {self.tif_path}")
            
            # Clean up
            for src in src_files_to_mosaic:
                src.close()
            for fp in temp_files:
                os.remove(fp)
                
        except Exception as e:
            logging.error(f"Exception during terrain download: {e}", exc_info=True)

    async def load(self):
        if not os.path.exists(self.tif_path):
            await self._download_srtm()
            
        if os.path.exists(self.tif_path):
            with rasterio.open(self.tif_path) as src:
                self.elevation_data = src.read(1)
                self.transform = src.transform
                logging.info(f"Terrain Matrix loaded. Shape: {self.elevation_data.shape}")

    def get_elevation_at(self, lng: float, lat: float) -> float:
        """Helper to get elevation given longitude and latitude using PyProj and rasterio."""
        if self.elevation_data is None or self.transform is None:
            return 0.0
            
        try:
            x, y = self.proj_transformer.transform(lng, lat)
            row, col = ~self.transform * (x, y)
            r, c = int(row), int(col)
            
            # Check bounds
            if 0 <= r < self.elevation_data.shape[0] and 0 <= c < self.elevation_data.shape[1]:
                return float(self.elevation_data[r, c])
        except Exception:
            pass
        return 0.0

    def get_movement_penalty(self, start_pos: list, end_pos: list) -> float:
        """Calculates rough movement penalty based on elevation delta (slope)."""
        el1 = self.get_elevation_at(start_pos[0], start_pos[1])
        el2 = self.get_elevation_at(end_pos[0], end_pos[1])
        
        # Simple slope calculation (assume delta of 1 meter elevation reduces speed)
        elevation_delta = abs(el2 - el1)
        
        # If moving up a steep hill (> 5m delta between local pixels), penalize heavily
        penalty = 1.0 - min(0.8, (elevation_delta * 0.05)) 
        return max(0.1, penalty) # Minimum 10% speed

    def is_los_blocked(self, pos1: list, pos2: list) -> bool:
        """
        Check if the line of sight between two geographic points is blocked by terrain.
        Uses height-aware ray sampling along the elevation matrix.
        """
        if self.elevation_data is None or self.transform is None:
            return False

        try:
            # Convert both points to raster indices
            x1, y1 = self.proj_transformer.transform(pos1[0], pos1[1])
            r1, c1 = ~self.transform * (x1, y1)
            
            x2, y2 = self.proj_transformer.transform(pos2[0], pos2[1])
            r2, c2 = ~self.transform * (x2, y2)

            h1 = self.get_elevation_at(pos1[0], pos1[1]) + 2.0 # Assume viewer height 2m
            h2 = self.get_elevation_at(pos2[0], pos2[1]) + 2.0 # Assume target height 2m

            # Sample 20 points along the line
            num_samples = 20
            rs = np.linspace(r1, r2, num_samples)
            cs = np.linspace(c1, c2, num_samples)
            hs = np.linspace(h1, h2, num_samples)

            for i in range(1, num_samples - 1):
                idx_r, idx_c = int(rs[i]), int(cs[i])
                if 0 <= idx_r < self.elevation_data.shape[0] and 0 <= idx_c < self.elevation_data.shape[1]:
                    terrain_h = float(self.elevation_data[idx_r, idx_c])
                    if terrain_h > hs[i]:
                        return True
        except Exception:
            pass
        return False
