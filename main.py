import geopandas as gpd
import math
import numpy as np

# from twod_prototype import SphereDrawer2D


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
            if country == "France":
                geom = list(geom.geoms)[1]
            else:
                geom = list(geom.geoms)[0]

        # Get longitude, latitude coordinates
        coords = list(geom.exterior.coords)

        # Remove last point if points are already circular
        if coords[0] == coords[-1]:
            coords = coords[:-1]

        # Convert to cartesion coordinates
        points = []
        for lon, lat in coords:
            points.append(geographic_to_cartesian(lat, lon))
        
        points = points[::-1]

        return points


def process_three_points(A ,B, C):
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    # print(A, B, C)

    u = B - A
    v = C - B
    r = B  # normal (unit sphere)

    # projection to tangent plane
    u_perp = u - np.dot(u, r) * r
    v_perp = v - np.dot(v, r) * r

    norm_u = np.linalg.norm(u_perp)
    norm_v = np.linalg.norm(v_perp)

    if norm_u == 0 or norm_v == 0:
        return 0

    # angle magnitude
    cos_theta = np.dot(u_perp, v_perp) / (norm_u * norm_v)
    cos_theta = np.clip(cos_theta, -1, 1)
    theta = math.acos(cos_theta)

    cross = np.cross(u_perp, v_perp)
    sign = np.sign(np.dot(cross, r))  # orientation

    return sign * theta


def calculate_area(points):
    N = len(points)
    total = 0

    for i in range(N):
        A = points[i - 1]
        B = points[i]
        C = points[(i + 1) % N]

        total += process_three_points(A, B, C)

    area = 2 * math.pi - total

    return area


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


def test(source, country, true_area):
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

    # Plot
    # plot = SphereDrawer2D()
    # points_2d = [(x, y) for x, y, z in points]
    # plot.set_points(points_2d)
    # plot.show()

    # Output results
    print("Calculated Area:", area)
    print("True Area:", true_area)
    print("Error:", str(round(100 * (area - true_area) / true_area, 2)) + "%")
    print()


def main():
    # Test octant
    source = "octant"
    country = None
    true_area = math.pi/2
    test(source, country, true_area)

    # Test Lesotho
    source = "country"
    country = "Lesotho"
    true_area = 30355
    test(source, country, true_area)

    # Test France
    source = "country"
    country = "France"
    true_area = 543941
    test(source, country, true_area)


if __name__ == "__main__":
    main()
