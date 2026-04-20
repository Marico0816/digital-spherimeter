import math
import numpy as np
import pyvista as pv

from main import calculate_area


RADIUS = 1.0

clicked_points = []
point_actors = []
line_actor = None
text_actor = None
fill_actor = None
plotter = None
sphere_mesh = None


def normalize(v):
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def display_to_world(x, y, z):
    """
    Convert display coordinates (x, y, z in [0,1]) to world coordinates.
    z=0 is near plane, z=1 is far plane.
    """
    renderer = plotter.renderer
    renderer.SetDisplayPoint(float(x), float(y), float(z))
    renderer.DisplayToWorld()
    world = renderer.GetWorldPoint()

    if abs(world[3]) < 1e-12:
        return None

    return np.array(world[:3]) / world[3]


def intersect_mouse_with_sphere(x, y, radius=RADIUS):
    """
    Shoot a ray through the mouse cursor and intersect it with the sphere.
    Returns the visible intersection point, or None if there is no hit.
    """
    p_near = display_to_world(x, y, 0.0)
    p_far = display_to_world(x, y, 1.0)

    if p_near is None or p_far is None:
        return None

    d = p_far - p_near
    d_norm = np.linalg.norm(d)
    if d_norm < 1e-12:
        return None
    d = d / d_norm

    # Solve ||p_near + t d||^2 = radius^2
    a = np.dot(d, d)
    b = 2.0 * np.dot(p_near, d)
    c = np.dot(p_near, p_near) - radius * radius

    disc = b * b - 4.0 * a * c
    if disc < 0:
        return None

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)

    # Keep intersections in front of the camera
    ts = [t for t in (t1, t2) if t > 0]
    if not ts:
        return None

    # Choose the closer visible hit
    t = min(ts)
    p = p_near + t * d
    return normalize(p) * radius


def on_left_button_press(*args):
    """
    Custom left-click handler that places a point exactly where the mouse ray
    hits the sphere.
    """
    interactor = plotter.iren.interactor
    x, y = interactor.GetEventPosition()

    point = intersect_mouse_with_sphere(x, y)
    if point is not None:
        add_clicked_point(point)


def geodesic_arc_points(p0, p1, n=100, radius=1.0):
    """
    Return n+1 points along the shorter geodesic (great-circle arc)
    from p0 to p1 on the sphere using spherical linear interpolation.
    """
    p0 = normalize(p0)
    p1 = normalize(p1)

    dot = np.clip(np.dot(p0, p1), -1.0, 1.0)
    omega = math.acos(dot)

    # If points are extremely close, just return a straight interpolation
    # projected back to the sphere.
    if omega < 1e-10:
        pts = []
        for t in np.linspace(0, 1, n + 1):
            p = normalize((1 - t) * p0 + t * p1) * radius
            pts.append(p)
        return np.array(pts)

    sin_omega = math.sin(omega)
    pts = []

    for t in np.linspace(0, 1, n + 1):
        a = math.sin((1 - t) * omega) / sin_omega
        b = math.sin(t * omega) / sin_omega
        p = a * p0 + b * p1
        pts.append(p * radius)

    return np.array(pts)


def build_geodesic_polyline(points, close=False, arc_resolution=100):
    """
    Build a polyline made of geodesic arcs between consecutive points.
    """
    if len(points) < 2:
        return None

    all_pts = []

    num_segments = len(points) if close else len(points) - 1

    for i in range(num_segments):
        p0 = points[i]
        p1 = points[(i + 1) % len(points)]

        arc = geodesic_arc_points(p0, p1, n=arc_resolution, radius=RADIUS)

        # Avoid duplicating endpoints between consecutive arcs
        if i > 0:
            arc = arc[1:]

        all_pts.append(arc)

    all_pts = np.vstack(all_pts)
    return pv.lines_from_points(all_pts, close=False)


def update_polyline():
    """
    Update the red boundary line connecting clicked points by geodesic arcs
    """
    global line_actor

    if line_actor is not None:
        plotter.remove_actor(line_actor)
        line_actor = None

    if len(clicked_points) >= 2:
        poly = build_geodesic_polyline(
            clicked_points,
            close=(len(clicked_points) >= 3),
            arc_resolution=100,
        )
        line_actor = plotter.add_mesh(poly, color="red", line_width=4)


def update_text():
    """
    Update the information text in the top-left corner
    Uses your original calculate_area() from main.py
    """
    global text_actor

    if text_actor is not None:
        plotter.remove_actor(text_actor)
        text_actor = None

    if len(clicked_points) >= 3:
        area = calculate_area(clicked_points)
    else:
        area = 0.0

    fraction = area / (4 * math.pi)

    message = (
        f"Points: {len(clicked_points)}\n"
        f"Area: {area:.6f}\n"
        f"Fraction of sphere: {fraction:.6%}\n"
        f"Controls:\n"
        f"  Left click: add point (counter-clockwise)\n"
        f"  Left hold and drag: change perspective\n"
        f"  u: undo\n"
        f"  c: clear\n"
        f"  q: quit"
    )

    text_actor = plotter.add_text(
        message,
        position="upper_left",
        font_size=30,
        color="black",
    )


def add_clicked_point(point):
    """
    Add a clicked point on the sphere
    """
    global clicked_points

    p = normalize(point) * RADIUS
    clicked_points.append(tuple(p))

    marker = pv.Sphere(radius=0.03, center=p)
    actor = plotter.add_mesh(marker, color="blue")
    point_actors.append(actor)

    update_polyline()
    update_fill()
    update_text()

    print(f"Added point {len(clicked_points)}: {tuple(p)}")


def undo_last():
    """
    Remove the last clicked point
    """
    if not clicked_points:
        return

    clicked_points.pop()

    actor = point_actors.pop()
    plotter.remove_actor(actor)

    update_polyline()
    update_fill()
    update_text()

    print("Undo last point")


def clear_all():
    """
    Clear all points and lines
    """
    global clicked_points, point_actors, line_actor, fill_actor

    for actor in point_actors:
        plotter.remove_actor(actor)
    clicked_points = []

    for actor in point_actors:
        plotter.remove_actor(actor)
    point_actors = []

    if line_actor is not None:
        plotter.remove_actor(line_actor)
        line_actor = None

    update_text()
    update_fill()

    print("Cleared all points")


def click_callback(point):
    """
    Callback for mouse click on sphere surface
    """
    if point is None:
        return

    add_clicked_point(point)


def spherical_polygon_orientation(points):
    """
    Estimate orientation of a spherical polygon.
    Positive means roughly counterclockwise with respect to the polygon normal.
    Returns a signed value; near 0 means ambiguous/degenerate.
    """
    if len(points) < 3:
        return 0.0

    pts = [normalize(p) for p in points]
    total = np.zeros(3)

    for i in range(len(pts)):
        p0 = pts[i]
        p1 = pts[(i + 1) % len(pts)]
        total += np.cross(p0, p1)

    centroid = normalize(np.sum(pts, axis=0))
    return float(np.dot(total, centroid))


def build_dense_boundary(points, arc_resolution=40):
    """
    Densify the spherical polygon boundary using geodesic arcs.
    Returns a sequence of boundary points on the sphere.
    """
    if len(points) < 3:
        return None

    dense = []
    n = len(points)
    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        arc = geodesic_arc_points(p0, p1, n=arc_resolution, radius=RADIUS)

        if i > 0:
            arc = arc[1:]  # avoid duplicate endpoint
        dense.append(arc)

    return np.vstack(dense)


def signed_area_2d(poly):
    """
    Signed area of a 2D polygon.
    """
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))


def polygon_reference_normal(points):
    """
    Robust reference normal from the ordered spherical polygon.
    Positive orientation corresponds to the intended CCW interior.
    """
    if len(points) < 3:
        return None

    pts = [normalize(p) for p in points]
    total = np.zeros(3)

    for i in range(len(pts)):
        p0 = pts[i]
        p1 = pts[(i + 1) % len(pts)]
        total += np.cross(p0, p1)

    nrm = np.linalg.norm(total)
    if nrm < 1e-10:
        return None

    return total / nrm


def local_tangent_basis(center):
    """
    Build an orthonormal basis (e1, e2) for the tangent plane at `center`.
    """
    c = normalize(center)

    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(c, ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])

    e1 = normalize(np.cross(ref, c))
    e2 = normalize(np.cross(c, e1))
    return e1, e2


def spherical_to_gnomonic(points, center):
    """
    Gnomonic projection from the sphere to the tangent plane at `center`.

    This only behaves well when all points lie in the same hemisphere as center,
    i.e. dot(center, p) > 0 for every boundary point.
    """
    c = normalize(center)
    e1, e2 = local_tangent_basis(c)

    coords_2d = []
    for p in points:
        p = normalize(p)
        denom = np.dot(c, p)

        # Outside visible hemisphere -> projection invalid
        if denom <= 1e-8:
            return None, None, None, None

        x = np.dot(p, e1) / denom
        y = np.dot(p, e2) / denom
        coords_2d.append([x, y])

    return np.array(coords_2d), e1, e2, c


def gnomonic_to_sphere(x, y, e1, e2, c, radius=1.0):
    """
    Inverse gnomonic map from tangent-plane coordinates back to the sphere.
    """
    v = c + x * e1 + y * e2
    return normalize(v) * radius


def build_filled_spherical_region(points, arc_resolution=40):
    """
    Build a filled mesh for a spherical polygon by:
      1. densifying the geodesic boundary,
      2. projecting with a gnomonic projection centered at a robust polygon normal,
      3. triangulating in 2D,
      4. mapping triangles back to the sphere.

    Returns None if the polygon is too ambiguous / too large for a single
    hemisphere-based fill.
    """
    if len(points) < 3:
        return None

    boundary3d = build_dense_boundary(points, arc_resolution=arc_resolution)
    if boundary3d is None or len(boundary3d) < 3:
        return None

    normal = polygon_reference_normal(points)
    if normal is None:
        return None

    # Make sure the intended interior is on the side of 'normal'
    boundary2d, e1, e2, c = spherical_to_gnomonic(boundary3d, normal)
    if boundary2d is None:
        return None

    # Ensure CCW in projection
    if signed_area_2d(boundary2d) < 0:
        boundary2d = boundary2d[::-1]
        boundary3d = boundary3d[::-1]

    pts3 = np.column_stack([boundary2d, np.zeros(len(boundary2d))])
    faces = np.hstack([[len(pts3)], np.arange(len(pts3))])
    poly = pv.PolyData(pts3, faces=faces)

    tri2d = poly.triangulate()

    sphere_pts = np.array([
        gnomonic_to_sphere(x, y, e1, e2, c, radius=RADIUS)
        for x, y, _ in tri2d.points
    ])

    return pv.PolyData(sphere_pts, faces=tri2d.faces)


def update_fill():
    """
    Shade the interior of the spherical region.
    Assumes points are intended to wrap counterclockwise.
    Only fills when the polygon is representable in one hemisphere.
    """
    global fill_actor

    if fill_actor is not None:
        plotter.remove_actor(fill_actor)
        fill_actor = None

    if len(clicked_points) < 3:
        return

    pts = clicked_points

    normal = polygon_reference_normal(pts)
    if normal is None:
        return

    fill_mesh = build_filled_spherical_region(pts, arc_resolution=40)
    if fill_mesh is not None:
        fill_actor = plotter.add_mesh(
            fill_mesh,
            color="red",
            opacity=0.25,
            smooth_shading=True,
            show_edges=False,
        )


def main():
    global plotter, sphere_mesh

    plotter = pv.Plotter(window_size=[1000, 800])

    # Create sphere
    sphere_mesh = pv.Sphere(radius=RADIUS, theta_resolution=200, phi_resolution=200)
    plotter.add_mesh(
        sphere_mesh,
        color="white",
        opacity=0.7,
        smooth_shading=True,
        pickable=False,   # we are no longer using PyVista's surface picker
    )

    plotter.add_axes()
    update_text()

    # Replace enable_surface_point_picking(...) with a custom mouse handler
    plotter.iren.interactor.AddObserver("LeftButtonPressEvent", on_left_button_press)

    # Keyboard shortcuts
    plotter.add_key_event("u", undo_last)
    plotter.add_key_event("c", clear_all)
    plotter.add_key_event("q", lambda: plotter.close())

    print("Left click on the sphere to add points.")
    print("Press 'u' to undo, 'c' to clear, 'q' to quit.")

    plotter.show()


if __name__ == "__main__":
    main()