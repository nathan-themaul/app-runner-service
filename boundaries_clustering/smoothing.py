from simplification.cutil import simplify_coords
import numpy as np
from shapely.geometry import LineString, Point, mapping, Polygon
from scipy.interpolate import UnivariateSpline, CubicSpline
from scipy.optimize import minimize
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler
def savgol_smoothing(points, tolerance=0.00000002):

    if len(points) < 5:
        return points  # Not enough points to apply smoothing

    # Simplify the path to remove minor deviations
    simplified_points = simplify_coords(points, tolerance)

    # The window_length for savgol_filter needs to be odd and less than the size of the data
    # A larger window_length means the filter considers more points in the dataset for each smoothing calculation, 
    # leading to a smoother overall result but potentially losing some of the finer details.
    window_length = min(5, len(simplified_points) - 1)
    if window_length % 2 == 0:
        window_length += 1  # Make it odd

    # Scale the points for more effective smoothing
    scaler = StandardScaler()
    scaled_points = scaler.fit_transform(simplified_points)

    # Savitzky-Golay smoothing algorithm
    # The polyorder is the degree of the polynomial; for example, a polyorder of 2 means that a quadratic polynomial is used for the local fitting.
    # A higher polynomial order can fit more complex variations in the data but may also lead to overfitting, 
    # where the smoothed curve starts to follow the noise in the data rather than the underlying trend.
    x_coords, y_coords = zip(*scaled_points)
    smooth_x = savgol_filter(x_coords, window_length=window_length, polyorder=2)
    smooth_y = savgol_filter(y_coords, window_length=window_length, polyorder=2)

    # Transform the coordinates back to the original scale
    smoothed_points = scaler.inverse_transform(np.column_stack([smooth_x, smooth_y]))
    
    return smoothed_points

def spline_smoothing(points, smoothing_factor=0.0000000000001):
    if len(points) < 3:
        # print('/!\\ skipped a boundary as it contains less than 3 points /!\\')
        return np.array(points) # Not enough points to fit a cubic spline

    # Calculate cumulative distance along the curve
    distances = [0]
    for i in range(1, len(points)):
        distances.append(distances[-1] + np.linalg.norm(np.array(points[i]) - np.array(points[i-1])))

    x_coords, y_coords = zip(*points)

    spline_x = UnivariateSpline(distances, x_coords, k=3, s=smoothing_factor)
    spline_y = UnivariateSpline(distances, y_coords, k=3, s=smoothing_factor)

    max_distance = distances[-1]
    distances_smooth = np.linspace(0, max_distance, len(points)*20)
    x_smooth = spline_x(distances_smooth)
    y_smooth = spline_y(distances_smooth)
    smooth_points = np.column_stack([x_smooth, y_smooth])
    # smooth_points = list(zip(x_smooth, y_smooth)) # returns a list of tuples

    return smooth_points

def chaikin_smoothing(points, iterations=5):
    """
    Smoothens a boundary using the Chaikin algorithm.

    :param points: The original list of points (as tuples of x, y coordinates).
    :param iterations: Number of times the algorithm is applied.
    :return: List of smoothed points.
    """
    if len(points) < 3:
        return points  # Not enough points to apply smoothing

    def refine(points):
        new_points = [points[0]]  # Keep the first point
        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]

            # Calculate two new points, 1/4th and 3/4th along the segment
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])

            new_points.extend([q, r])
        new_points.append(points[-1])  # Keep the last point
        return new_points

    for _ in range(iterations):
        points = refine(points)

    return points

def opti_spline_smoothing(boundary, opposite_boundary, smooth_factor=0.5, segment_length=5, penalty_scale=1):
    boundary1_points = np.array(boundary)
    boundary2_points = np.array(opposite_boundary)

    # Create a polygon from the lane boundaries for constraint checking
    lane_polygon = Polygon(np.vstack((boundary1_points, boundary2_points[::-1], boundary1_points[0])))

    # Process in segments to simplify the problem
    smoothed_points = []
    for i in range(0, len(boundary1_points), segment_length):
        segment = boundary1_points[i:i+segment_length]
        if len(segment) < 2:
            continue

        optimized_segment = minimize(
            lambda points: loss_function(points, segment, lane_polygon, penalty_scale),
            x0=segment.flatten(),
            method='L-BFGS-B',
            options={'ftol': 1e-6, 'maxiter': 1000}
        ).x.reshape(-1, 2)

        # Post-optimization check and adjustment
        optimized_segment = adjust_points_post_optimization(optimized_segment, lane_polygon)
        smoothed_points.extend(optimized_segment)

    # Fit a spline to the combined optimized segments
    t = np.linspace(0, 1, len(smoothed_points))
    optimized_cs = CubicSpline(t, smoothed_points, axis=0)
    smooth_t = np.linspace(0, 1, int(len(boundary1_points) * (1 + smooth_factor)))
    final_smoothed_points = optimized_cs(smooth_t)

    # Visualizing the boundaries and the optimized smoothed points
    # plt.figure(figsize=(10, 6))
    # plt.scatter(*zip(*boundary1_points), c='blue', label='Original Boundary Points')
    # plt.scatter(*zip(*smoothed_points), c='red', label='Smoothed Points')
    # plt.plot(*lane_polygon.exterior.xy, c='green', label='Lane Boundary')
    # plt.legend()
    # plt.title("Lane Boundary Smoothing Visualization")
    # plt.xlabel("X Coordinate")
    # plt.ylabel("Y Coordinate")
    # plt.show()
    return np.array(final_smoothed_points)


def loss_function(points, original_points, lane_polygon, penalty_scale):
    reshaped_points = points.reshape(-1, 2)
    smoothness_loss = np.sum((reshaped_points - original_points)**2)
    constraint_loss = 0

    for point in reshaped_points:
        if not lane_polygon.contains(Point(point)):
            distance = lane_polygon.exterior.distance(Point(point))
            constraint_loss += penalty_scale * distance

    return smoothness_loss + constraint_loss

def adjust_points_post_optimization(points, lane_polygon):
    adjusted_points = []
    for point in points:
        if lane_polygon.contains(Point(point)):
            # Adjust the point to the nearest point on the boundary
            nearest_point = nearest_boundary_point(point, lane_polygon)
            adjusted_points.append(nearest_point)
        else:
            adjusted_points.append(point)
    return adjusted_points

def nearest_boundary_point(point, polygon):
    """
    Find the nearest point on the boundary of a polygon to a given point.

    Args:
    point (tuple): The point for which the nearest boundary point is to be found.
    polygon (Polygon): A Shapely Polygon object representing the lane boundary.

    Returns:
    tuple: The nearest point on the polygon boundary to the given point.
    """
    point = Point(point)
    boundary = polygon.boundary
    nearest_point = boundary.interpolate(boundary.project(point))
    return nearest_point.x, nearest_point.y

def find_corresponding_boundary(data, lane_id):
    # Logic to find the corresponding boundary points based on lane ID
    for key, value in data.items():
        if value['lanes'][0] == lane_id and key != str(lane_id):
            return value['coordinates']
    return None

from scipy.interpolate import splprep, splev

def spl_smoothing(points, smoothing_factor=0.00000000001, num_points=100):
    if len(points) < 3:
        return points  # Not enough points to apply smoothing
    points = np.array(points)
    tck, u = splprep([points[:,0], points[:,1]], s=smoothing_factor)
    u_new = np.linspace(u.min(), u.max(), num_points)
    new_points = splev(u_new, tck)
    return list(zip(new_points[0], new_points[1]))

def smooth_boundaries(boundaries, method):
    """
    Apply smoothing to each boundary and retain the original points.

    :param boundaries: Dictionary of boundaries, each containing points and associated lanes.
    :param smoothing_factor: Factor to control the smoothing level.
    :return: A dictionary with original and smoothed points for each boundary.
    """
    smoothed_boundaries = {}

    for boundary_key, data in boundaries.items():
        coordinates = data['coordinates']
        boundary_data = {'original_points': coordinates}
        
        if coordinates:  # Check if there are points in the boundary
            if method == "univariate":
                smoothed_points = spline_smoothing(coordinates)
            elif method == "savgol":
                smoothed_points = savgol_smoothing(coordinates)
            elif method == "chaikin":
                smoothed_points = chaikin_smoothing(coordinates)
            elif method == "spl":
                smoothed_points = spl_smoothing(coordinates)
            elif method == "opti_spline":
                other_boundary = None
                if len(data['lanes']) == 1:
                    other_boundary = find_corresponding_boundary(boundaries, data['lanes'][0])
                    if other_boundary and len(other_boundary) > 1:
                        smoothed_points = opti_spline_smoothing(coordinates, other_boundary)
                    else:
                        smoothed_points=coordinates
                else:
                    smoothed_points = coordinates
            else: 
                smoothed_points = coordinates
            
            boundary_data['smoothed_points'] = smoothed_points

        # Retain the lanes information
        boundary_data['lanes'] = data['lanes']
        smoothed_boundaries[boundary_key] = boundary_data

    return smoothed_boundaries