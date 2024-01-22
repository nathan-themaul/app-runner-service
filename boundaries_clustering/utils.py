import numpy as np
from scipy.spatial.distance import cdist, euclidean

###### Functions for putting collinear groups together ######
def calculate_extremity_directions(points):
    """Calculate the direction vectors for the start and end segments of the cluster."""
    if len(points) < 2:
        return None, None  # Not enough points to determine a direction

    # Start direction
    start_direction = np.array(points[1]) - np.array(points[0])
    if np.all(start_direction == 0):
        print('points:', points)
    start_direction /= np.linalg.norm(start_direction)

    # End direction
    end_direction = np.array(points[-1]) - np.array(points[-2])
    end_direction /= np.linalg.norm(end_direction)

    return start_direction, end_direction

def are_extremities_collinear(direction1, direction2):
    """Check if the extremities are collinear."""
    return abs(np.dot(direction1, direction2)) > 0.99  # Adjust threshold as needed

def are_points_close(point1, point2, threshold):
    """Check if two points are within a certain distance."""
    return np.linalg.norm(np.array(point1) - np.array(point2)) < threshold

def are_extremities_compatible(start_dir1, end_dir1, start_dir2, end_dir2, point1_start, point1_end, point2_start, point2_end, proximity_threshold):
    """Check if extremities are both collinear and within proximity."""
    return ((are_extremities_collinear(start_dir1, start_dir2) and are_points_close(point1_start, point2_start, proximity_threshold)) or 
            (are_extremities_collinear(start_dir1, end_dir2) and are_points_close(point1_start, point2_end, proximity_threshold)) or 
            (are_extremities_collinear(end_dir1, start_dir2) and are_points_close(point1_end, point2_start, proximity_threshold)) or 
            (are_extremities_collinear(end_dir1, end_dir2) and are_points_close(point1_end, point2_end, proximity_threshold)))

###### Functions for the main algorithm ######
def findClosestPoints(targetPoint, targetGroup, allGroups, maxDistance):
    potentialMatches = []

    for group, points in allGroups.items():
        if group != targetGroup:
            distances = cdist([targetPoint], points)
            minDistance = np.min(distances)
            if minDistance < maxDistance:
                closestPoint = points[np.argmin(distances)]
                potentialMatches.append(closestPoint)
    
    return potentialMatches

def calculateDirection(points, index):
    if index == 0:
        return np.array(points[index+1]) - np.array(points[index])
    else:
        return np.array(points[index]) - np.array(points[index-1])

def evaluateDistance(pointA, pointB):
    return np.linalg.norm(np.array(pointA) - np.array(pointB))

def evaluateParallelism(directionA, directionB):
    unitA = directionA / np.linalg.norm(directionA)
    unitB = directionB / np.linalg.norm(directionB)
    # we use abs() as we don't want to take the direction into account, we only want to check if they are parallel
    return abs(np.dot(unitA, unitB))  # Dot product for parallelism

def evaluateScore(distance, parallelism, max_distance):
    # Higher parallelism and lower distance give higher score
    # Define weights
    weight_parallelism = 0.4
    weight_distance = 1 - weight_parallelism

    # Normalize distance (assuming distance is always positive)
    # The normalization here is to bring the distance to a comparable scale as parallelism
    normalized_distance = distance / max_distance  # max_distance is the maximum expected distance

    # Invert distance as lower distance should result in higher score
    inverse_distance = 1 - normalized_distance

    # Calculate weighted score
    score = (weight_parallelism * parallelism) + (weight_distance * inverse_distance)
    return score

def addToBoundaries(groupA, pointA, groupB, groupABC, boundaries, lanes):
    # Define laneKeys and groupKeys as arrays
    laneKeys = [[min(groupA, groupB), max(groupA, groupB)]]
    groupKey = [groupA, groupB]
    
    if groupABC is not None:
        laneKeys = [[min(groupA, groupABC[0]), max(groupA, groupABC[0])], [min(groupA, groupABC[2]), max(groupA, groupABC[2])]]
        groupKey = groupABC

    # Convert groupKey to a string to use as a dictionary key
    groupKeyStr = str(groupKey)

    if groupKeyStr not in boundaries:
        boundaries[groupKeyStr] = {'coordinates': [], 'lanes': laneKeys}

    if pointA not in boundaries[groupKeyStr]['coordinates']:
        boundaries[groupKeyStr]['coordinates'].append(pointA)

    # for each entry in laneKeys, if the entry is not already in the dictionary lanes, add it
    for laneKey in laneKeys:
        laneKeyStr = str(laneKey)
        if laneKeyStr not in lanes:
            lanes[laneKeyStr] = {'centerline': []}