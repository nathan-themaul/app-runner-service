import numpy as np

# Puts lanes points back in order after processing
def sort_path(points):
    """Sort points in a complex path based on the nearest neighbor approach, starting with the westernmost point."""
    if not points:
        return []

    # Find the westernmost point (minimum x-coordinate)
    start_point = min(points, key=lambda p: p[0])
    sorted_points = [start_point]
    points.remove(start_point)

    while points:
        last_point = sorted_points[-1]
        # Find the nearest next point
        nearest_next_point = min(points, key=lambda p: np.linalg.norm(np.array(p) - np.array(last_point)))
        sorted_points.append(nearest_next_point)
        points.remove(nearest_next_point)

    return sorted_points

def sort_all_boundaries(boundaries):
    """Sorts the coordinates in each boundary of each lane."""
    sorted_boundaries = {}

    for boundary_key, data in boundaries.items():
        # Sort the coordinates for each lane
        sorted_coordinates = sort_path(data['coordinates'].copy())
        sorted_boundaries[boundary_key] = {
            'coordinates': sorted_coordinates,
            'lanes': data['lanes']
        }

    return sorted_boundaries