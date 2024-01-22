import numpy as np
from scipy.interpolate import UnivariateSpline
from shapely.geometry import LineString, Point


def find_centerline_spline(spline_x1, spline_y1, spline_x2, spline_y2, max_distance1, max_distance2, num_points=200):
    if (not max_distance1 or not max_distance2):
        return [], [], 0

    max_distance = max(max_distance1, max_distance2)
    distances = np.linspace(0, max_distance, num_points)

    # Evaluate both splines at these distances
    x1, y1 = spline_x1(distances), spline_y1(distances)
    x2, y2 = spline_x2(distances), spline_y2(distances)

    # Calculate simple midpoints
    x_centerline = (x1 + x2) / 2
    y_centerline = (y1 + y2) / 2

    # Parameterize centerline by cumulative distance
    distances = [0]
    for i in range(1, len(x_centerline)):
        distances.append(distances[-1] + np.linalg.norm([x_centerline[i] - x_centerline[i-1], y_centerline[i] - y_centerline[i-1]]))

    # Fit splines to the centerline
    spline_center_x = UnivariateSpline(distances, x_centerline, k=3, s=0)
    spline_center_y = UnivariateSpline(distances, y_centerline, k=3, s=0)

    return spline_center_x, spline_center_y, max_distance

def find_centerlines_for_lanes(smoothed_lanes):
    """
    Find and store the centerline spline for each lane.

    :param smoothed_lanes: Dictionary of lanes with smoothed boundary splines.
    :return: Updated dictionary with added centerline splines for each lane.
    """
    for laneKey, groups in smoothed_lanes.items():
        # Assuming each lane has two groups representing two boundaries
        groupKeys = list(groups.keys())
        
        # Retrieve splines for both boundaries
        spline_x1, spline_y1, max_distance1 = groups[groupKeys[0]]['spline_x'], groups[groupKeys[0]]['spline_y'], groups[groupKeys[0]]['boundary_max_distance']
        spline_x2, spline_y2, max_distance2 = groups[groupKeys[1]]['spline_x'], groups[groupKeys[1]]['spline_y'], groups[groupKeys[1]]['boundary_max_distance']
        # Fit a spline to centerline points
        spline_center_x, spline_center_y, max_distance = find_centerline_spline(spline_x1, spline_y1, spline_x2, spline_y2, max_distance1, max_distance2)

        # Store the centerline spline in the lane data
        smoothed_lanes[laneKey]['centerline'] = {'spline_x': spline_center_x, 'spline_y': spline_center_y, 'centerline_max_distance': max_distance}

    return smoothed_lanes

from scipy.interpolate import interp1d

def interpolate_boundary(boundary, target_length):
    x, y = zip(*boundary)
    distance = np.linspace(0, 1, len(boundary))
    target_distance = np.linspace(0, 1, target_length)

    f_x = interp1d(distance, x, kind='linear')
    f_y = interp1d(distance, y, kind='linear')

    new_x = f_x(target_distance)
    new_y = f_y(target_distance)

    return list(zip(new_x, new_y))

def calculate_pairs_middle_centerline(boundary1, boundary2):
    max_length = max(len(boundary1), len(boundary2))
    boundary1 = interpolate_boundary(boundary1, max_length)
    boundary2 = interpolate_boundary(boundary2, max_length)

    centerline = [( (p1[0]+p2[0])/2, (p1[1]+p2[1])/2 ) for p1, p2 in zip(boundary1, boundary2)]
    return centerline

import ast

def get_boundaries_by_laneId(boundaries, laneId):
    boundaries_by_laneId = []
    for boundaryId, data in boundaries.items():
        # Convert the string representation of laneId to a list
        laneId_list = ast.literal_eval(laneId)
        if laneId_list in data['lanes']:
            boundaries_by_laneId.append(data['smoothed_points'])
    return boundaries_by_laneId

def calculate_centerlines(boundaries, lanes, method=None):
    for key, data in lanes.items():
        # Find the boundaries that have the lane key in boundary['lanes']
        lane_boundaries = get_boundaries_by_laneId(boundaries, key)

        # If there are exactly two boundaries, calculate the centerline
        if len(lane_boundaries) == 2:

            # Check if each boundary has at least two points
            if all(len(boundary) >= 2 for boundary in lane_boundaries):
                if method == 'pairs_middle':
                    centerline = calculate_pairs_middle_centerline(lane_boundaries[0], lane_boundaries[1])
                elif method == 'bezier':
                    centerline = calculate_bezier_centerline(lane_boundaries[0], lane_boundaries[1])
                elif method == 'perpendicular':
                    centerline = calculate_perpendicular_centerline(lane_boundaries[0], lane_boundaries[1])
                else:
                    centerline = calculate_pairs_middle_centerline(lane_boundaries[0], lane_boundaries[1])
                lanes[key]['centerline'] = centerline
            # else:
                # print(f"Lane {key} has a boundary with insufficient points.")
        # else:
            # print(f"Lane {key} does not have exactly two boundaries.")
    return lanes

import bezier
from simplification.cutil import simplify_coords

def fit_bezier_curve(boundary, tolerance=0.000000001):
    if isinstance(boundary, np.ndarray) and boundary.shape[0] == 2:
        boundary = boundary.T

    simplified_boundary = simplify_coords(boundary, tolerance)

    # Format for Bezier curve
    nodes = np.asfortranarray(simplified_boundary.T)

    # Adjust the degree of the curve based on the number of nodes
    degree = (len(simplified_boundary) - 1)  # Limiting degree to a reasonable maximum
    curve = bezier.Curve(nodes, degree=degree)
    return curve

def calculate_bezier_centerline(boundary1, boundary2, num_points=100):
    curve1 = fit_bezier_curve(np.array(boundary1))
    curve2 = fit_bezier_curve(np.array(boundary2))
    centerline = calculate_bezier_centerline(curve1, curve2)
    centerline = []
    for s in np.linspace(0, 1, num_points):
        point1 = curve1.evaluate(s)
        point2 = curve2.evaluate(s)
        midpoint = (point1 + point2) / 2
        centerline.append(midpoint[:, 0].tolist())
    return centerline

def find_perpendicular_midpoint(point, opposite_line):
    # Find the closest point on the opposite boundary line
    closest_point = opposite_line.interpolate(opposite_line.project(Point(point)))
    return [(point[0] + closest_point.x) / 2, (point[1] + closest_point.y) / 2]

def calculate_perpendicular_centerline(boundary1, boundary2, num_points=100):
    line1 = LineString(boundary1)
    line2 = LineString(boundary2)

    # Sample points along one boundary (you can choose either boundary)
    sampled_points = [line1.interpolate(fraction, normalized=True) for fraction in np.linspace(0, 1, num_points)]
    
    centerline_points = [find_perpendicular_midpoint((point.x, point.y), line2) for point in sampled_points]
    return centerline_points

import itertools

def calculate_midpoint(point1, point2):
    return [(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2]

def prepare_endpoints(lanes):
    endpoints = []
    for lane_id, lane in lanes.items():
        if lane['centerline']:
            # calculate lenght of lane['centerline'] which is a list of coordinates
            segment_length = sum([np.linalg.norm(np.array(point1) - np.array(point2)) for point1, point2 in zip(lane['centerline'][:-1], lane['centerline'][1:])])
            print('segment length:', segment_length)
            # Add both ends of the centerline
            for end in [lane['centerline'][0], lane['centerline'][-1]]:
                endpoints.append({'location': end, 'lane': lane_id, 'segment_length': segment_length})
    return endpoints

def create_nodes_from_endpoints(endpoints, threshold=0.00008):
    nodes = []
    used_endpoints = set()

    for i, endpoint1 in enumerate(endpoints):
        if i in used_endpoints:
            continue

        # Group nearby endpoints
        group = [endpoint1]
        for j, endpoint2 in enumerate(endpoints):
            if j != i and j not in used_endpoints and endpoint2['segment_length'] > threshold:
                distance = np.linalg.norm(np.array(endpoint1['location']) - np.array(endpoint2['location']))
                if distance < threshold:
                    group.append(endpoint2)
                    used_endpoints.add(j)

        if len(group) > 1:
            # Calculate the centroid of the group
            x_coords, y_coords = zip(*[ep['location'] for ep in group])
            centroid = [sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)]
            
            # Create node with connections
            node = {
                'location': centroid,
                'connections': [{'lane': ep['lane'], 'line': [ep['location'], centroid]} for ep in group]
            }
            nodes.append(node)

    return nodes

def link_centerlines_to_central_nodes(lanes, central_nodes, threshold=0.00003):
    for lane_id, lane in lanes.items():
        if not lane['centerline']:
            continue

        for end in [lane['centerline'][0], lane['centerline'][-1]]:
            closest_node, min_distance = None, float('inf')
            for node in central_nodes:
                distance = np.linalg.norm(np.array(node['location']) - np.array(end))
                if distance < min_distance:
                    closest_node, min_distance = node, distance

            if closest_node and min_distance < threshold:
                lane.setdefault('connected_nodes', []).append(closest_node)

    return lanes

def serialize_spline(spline):
    return {
        'knots': spline.get_knots().tolist(),
        'coefficients': spline.get_coeffs().tolist(),
        'degree': spline.get_degree()
    }