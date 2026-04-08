import math

def geo_to_meters(lat, lon, anchor_lat, anchor_lon):
    """
    Converts Lon/Lat to relative meters from an anchor point (SW corner).
    Uses a simple Equirectangular projection suitable for local tactical maps.
    """
    # Earth radius in meters
    R = 6378137.0
    
    # 1 degree of latitude in meters (constant)
    lat_m_per_deg = 111319.9
    
    # 1 degree of longitude in meters (varies by latitude)
    lon_m_per_deg = lat_m_per_deg * math.cos(math.radians(lat))
    
    delta_lat = lat - anchor_lat
    delta_lon = lon - anchor_lon
    
    x = delta_lon * lon_m_per_deg
    y = delta_lat * lat_m_per_deg
    
    return round(x, 2), round(y, 2)

if __name__ == "__main__":
    # Test: Antietam Bounds
    # SW: -77.75, 39.45 | NE: -77.70, 39.50
    sw_lon, sw_lat = -77.75, 39.45
    ne_lon, ne_lat = -77.70, 39.50
    
    # Distance in meters
    dist_x, dist_y = geo_to_meters(ne_lat, ne_lon, sw_lat, sw_lon)
    print(f"Antietam Battle Area (Meters): {dist_x}m x {dist_y}m")
    print(f"Unreal Units (cm): {dist_x * 100} x {dist_y * 100}")
