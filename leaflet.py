import geopandas as gpd
from shapely.geometry import Polygon

gdf = gdf.dropna(subset=["rings"]).copy()
gdf["geometry"] = gdf["rings"].apply(lambda r: Polygon(r[0], r[1:] or None))
gdf["DATEMODIFIED"] = pd.to_datetime(gdf["DATEMODIFIED"], unit="ms")
out = gpd.GeoDataFrame(gdf.drop(columns="rings"), geometry="geometry", crs=27700)
out["area_m2"] = out.geometry.area          # SHAPE.AREA is 0 in the service
out.to_crs(4326).to_file("applications.geojson", driver="GeoJSON")