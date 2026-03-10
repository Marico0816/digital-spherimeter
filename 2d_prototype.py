import math
import matplotlib.pyplot as plt

from main import calculate_area


class SphereDrawer2D:
    def __init__(self):
        # Initialize points
        self.points_2d = []
        
        # Draw figure
        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.area_text = self.ax.text(0, 1.25, "Area: N/A", ha="center", fontsize=12)
        self.space_text = self.ax.text(0.8, 1.35, "space = close curve and")
        self.space_text_2 = self.ax.text(1.20, 1.25, "compute area")
        self.c_text = self.ax.text(1.0, 1.13, "c = clear")

        # Draw unit circle
        circle = plt.Circle((0, 0), 1, fill=False, linewidth=2)
        self.ax.add_patch(circle)

        # Line for drawn curve
        self.line, = self.ax.plot([], [], marker="o")

        # Set events
        self.fig.canvas.mpl_connect("button_press_event", self.on_mouse_press)
        # self.fig.canvas.mpl_connect("button_release_event", self.on_mouse_release)
        # self.fig.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key_press)

    def update_plot(self):
        """
        Refresh the plot display
        """
        # Convert points to 2 separate lists
        if len(self.points_2d) > 0:
            xs = [p[0] for p in self.points_2d]
            ys = [p[1] for p in self.points_2d]
        else:
            xs = []
            ys = []
        
        # Redraw line
        self.line.set_data(xs, ys)
        self.fig.canvas.draw_idle()

    def convert_2D_to_3D(self, x, y):
        return (x, y, math.sqrt(1 - x * x - y * y))

    def calculate_area(self):
        """
        Compute area
        """
        points_3d = [self.convert_2D_to_3D(x, y) for x, y in self.points_2d]
        area = calculate_area(points_3d)
        self.area_text.set_text(f"Area: {area:.6f}")
        self.points_2d = []

    def add_point(self, x, y):
        """
        Add point if within domain
        """
        if x * x + y * y <= 1:
            self.points_2d.append((x, y))
            self.update_plot()

    def add_point_from_event(self, event):
        """
        Convert a matplotlib mouse event into a point
        """
        x = event.xdata
        y = event.ydata
        self.add_point(x, y)
    
    def add_finishing_point(self):
        """
        Finish curve by connecting last point to first point
        """
        if len(self.points_2d) > 2:
            x = self.points_2d[0][0]
            y = self.points_2d[0][1]
            self.add_point(x, y)
            self.calculate_area()

    def clear_points(self):
        self.points_2d = []
        self.update_plot()

    def on_mouse_press(self, event):
        """
        Add point when mouse button 1 (left click) is pressed
        """
        if event.button == 1:
            self.add_point_from_event(event)
    
    def on_key_press(self, event):
        """
        Finish curve when space is pressed
        """
        if event.key == " ":
            self.add_finishing_point()
        elif event.key == "c":
            self.clear_points()

    def show(self):
        """
        Display plot
        """
        plt.show()


def main():
    sphere = SphereDrawer2D()
    sphere.show()


if __name__ == "__main__":
    main()