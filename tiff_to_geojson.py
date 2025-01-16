import rasterio
import geopandas as gpd
import numpy as np
from colorsys import hsv_to_rgb
from rasterio.features import shapes
import folium
import webbrowser

# File name of the TIFF raster
tiff_name = 'Drought_Map_r.tif'

# Open the TIFF file and get metadata
with rasterio.open(tiff_name) as src:
    meta = src.meta
    c = str(meta['crs'])
    c_s = c.split(':')
    c_s[1]  # Extract the EPSG code

    mask = None
    image = src.read(1)  # Read the first band
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for s, v in shapes(image, mask=mask, transform=src.transform)
    )

# Convert raster data to GeoDataFrame
geoms = list(results)
gpd_polygonized_raster = gpd.GeoDataFrame.from_features(geoms, crs=c)
gpd_polygonized_raster = gpd_polygonized_raster[gpd_polygonized_raster['raster_val'] > 0]  # Filter valid values

# Define a function for pseudocoloring
def pseudocolor(val, minval, maxval):
    """Convert val in range minval..maxval to a color between Red and Green in HSV."""
    h = (float(val - minval) / (maxval - minval)) * 120
    r, g, b = hsv_to_rgb(h / 360, 1., 1.)
    return int(r * 255), int(g * 255), int(b * 255)

# Convert RGB to HEX
def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

# Define min and max values for pseudocolor
minval = 1
maxval = 5

# Add colors to the GeoDataFrame
for i, row in gpd_polygonized_raster.iterrows():
    gpd_polygonized_raster.loc[i, 'color'] = rgb_to_hex(pseudocolor(row['raster_val'], minval, maxval))

gpd_polygonized_raster['id'] = gpd_polygonized_raster.index

# Ensure CRS is in EPSG:4326 for visualization
if gpd_polygonized_raster.crs.to_string() != "EPSG:4326":
    gpd_polygonized_raster = gpd_polygonized_raster.to_crs("EPSG:4326")

# Initialize the map at the center of the data
map_center = [
    gpd_polygonized_raster.geometry.centroid.y.mean(),
    gpd_polygonized_raster.geometry.centroid.x.mean()
]
m = folium.Map(location=map_center, zoom_start=10)

# Add polygons to the map
for _, row in gpd_polygonized_raster.iterrows():
    folium.GeoJson(
        row['geometry'].__geo_interface__,
        style_function=lambda feature, color=row['color']: {
            'fillColor': f"#{color}",  # Correct HEX color format
            'color': 'black',         # Border color
            'weight': 1,
            'fillOpacity': 0.7
        }
    ).add_to(m)

# Save the map to an HTML file
output_file = "map_output.html"
m.save(output_file)

# Open the saved map in a browser
webbrowser.open(output_file)
