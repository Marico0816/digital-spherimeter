import math
import numpy as np
import pyvista as pv

from main import calculate_area


RADIUS = 1.0

clicked_points = []
point_actors = []
line_actor = None
text_actor = None
plotter = None


def normalize(v):
    """
    Normalize a vector to length 1
    """
    v = np.array(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


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
        f"  Left click: add point\n"
        f"  u: undo\n"
        f"  c: clear\n"
        f"  q: quit"
    )

    text_actor = plotter.add_text(
        message,
        position="upper_left",
        font_size=12,
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
    update_text()

    print("Undo last point")


def clear_all():
    """
    Clear all points and lines
    """
    global clicked_points, point_actors, line_actor

    clicked_points = []

    for actor in point_actors:
        plotter.remove_actor(actor)
    point_actors = []

    if line_actor is not None:
        plotter.remove_actor(line_actor)
        line_actor = None

    update_text()

    print("Cleared all points")


def click_callback(point):
    """
    Callback for mouse click on sphere surface
    """
    if point is None:
        return

    add_clicked_point(point)


def main():
    global plotter

    plotter = pv.Plotter(window_size=[1000, 800])

    # Create sphere
    sphere = pv.Sphere(radius=RADIUS, theta_resolution=120, phi_resolution=120)
    plotter.add_mesh(
        sphere,
        color="white",
        opacity=0.7,
        smooth_shading=True,
    )

    plotter.add_axes()
    update_text()

    # Enable clicking on sphere surface
    plotter.enable_surface_point_picking(
        callback=click_callback,
        left_clicking=True,
        show_point=False,
        show_message=False,
    )

    # Keyboard shortcuts
    plotter.add_key_event("u", undo_last)
    plotter.add_key_event("c", clear_all)
    plotter.add_key_event("q", lambda: plotter.close())

    print("Left click on the sphere to add points.")
    print("Press 'u' to undo, 'c' to clear, 'q' to quit.")

    plotter.show()


if __name__ == "__main__":
    main()
