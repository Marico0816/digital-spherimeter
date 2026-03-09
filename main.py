import geopandas as gpd
import math


def geographic_to_cartesian(lat, lon):
    """
    Converts latitude, longitude coordinates to cartesian coordinates
    """
    # Convert from degrees to radians
    lat = math.radians(lat)
    lon = math.radians(lon)

    # Convert to cartesian coords
    x = math.cos(lat) * math.cos(lon)
    y = math.cos(lat) * math.sin(lon)
    z = math.sin(lat)

    return (x, y, z)


def process_data(source_type, country=None):
    """
    Reads and formats data depending on the source
    Returns an array of 3D points [(x1, y1, z1), (x2, y2, z2), ...] denoting points on the unit sphere centered at the origin
    If source_type = "octant", returns the boundary of the first octant
    If source_type = "country", returns the border of the specified country
    """

    # Most basic test
    if source_type == "octant":
        return [(1, 0, 0), (0, 1, 0), (0, 0, 1)]

    # Country
    if source_type == "country":
        # Check if country was given
        if country is None:
            print("please specify a country")
            return []

        # Load data
        gdf = gpd.read_file("ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")

        # Get specific country data
        if gdf[gdf["ADMIN"] == country].empty:
            print("Invalid country")
            return []
        geom = gdf[gdf["ADMIN"] == country].iloc[0].geometry            

        # If the country has multiple parts, take the first one for now; later, we can loop over all parts
        if geom.geom_type == "MultiPolygon":
            geom = list(geom.geoms)[0]

        # Get longitude, latitude coordinates
        coords = list(geom.exterior.coords)

        # Convert to cartesion coordinates
        points = []
        for lon, lat in coords:
            points.append(geographic_to_cartesian(lat, lon))

        return points


def process_three_points():
    """
    Processes a single set of three points
    """


def calculate_area(points):
    """
    Iterates over sets of three points along curve
    """
    return 1


def rescale(area, source):
    """
    Rescale the calculated area from unit sphere area to actual area if needed
    """
    # Default no scale
    radius = 1

    # If source is a country, use Earth's radius in kilometers
    if source == "country":
        radius = 6371
    
    # Rescale area
    area = area * radius * radius

    return area


def test(source, country, true_areas):
    """
    Single testing unit
    """
    print()
    if source == "country":
        print("Testing:", country)
    else:
        print("Testing:", source)

    # Get points from source
    points = process_data(source, country)
    print("Points:", points)

    # Calculate area
    area = calculate_area(points)

    # Rescale
    area = rescale(area, source)

    # Output results
    print("Calculated Area:", area)
    true_area = true_areas[(source, country)]
    print("True Area:", true_area)
    print("Error:", str(round(100 * (area - true_area) / true_area, 2)) + "%")
    print()


def main():
    # Dictionary of true areas
    true_areas = {("octant", None): math.pi/2, ("country", "Lesotho"): 30355}

    # Test octant
    source = "octant"
    country = None
    test(source, country, true_areas)

    # Test Lesotho
    source = "country"
    country = "Lesotho"
    test(source, country, true_areas)


if __name__ == "__main__":
    main()
