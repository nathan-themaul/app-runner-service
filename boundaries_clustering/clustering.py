from scipy.spatial.distance import cdist
from database import get_dataset
from sklearn.cluster import DBSCAN
from utils import *

# clustering related functions
def get_clustering():
    # PART 1 : getting the points
    dataset = get_dataset()

    # PART 2 : cluster using distance between points

    # DBSCAN
    db = DBSCAN(eps=0.000025, min_samples=3).fit(dataset)
    labels = db.labels_

    # Plotting clusters
    # plot_dbscan_clusters(dataset, labels)

    # Organizing points into groups
    groupedPoints = {}
    for label, point in zip(labels, dataset):
        if label != -1:  # Excluding noise points
            if label not in groupedPoints:
                groupedPoints[label] = []
            groupedPoints[label].append(tuple(point))

    # Define your proximity threshold
    proximity_threshold = 0.00003  # Adjust based on your dataset

    # Filtering duplicate points
    filtered_data = {}
    for key, points in groupedPoints.items():
        seen = set()
        filtered_points = []
        for point in points:
            if point not in seen:
                seen.add(point)
                filtered_points.append(point)
        filtered_data[key] = filtered_points

    # Calculate extremity directions for each cluster
    extremity_directions = {label: calculate_extremity_directions(filtered_data[label]) for label in filtered_data}

    # Identify clusters to merge based on collinearity of extremities
    clusters_to_merge = []
    merged_labels = set()  # Set to keep track of merged or to-be-merged labels

    for label1, (start_dir1, end_dir1) in extremity_directions.items():
        points1 = filtered_data[label1]
        for label2, (start_dir2, end_dir2) in extremity_directions.items():
            points2 = filtered_data[label2]
            if label1 != label2 and label1 not in merged_labels and label2 not in merged_labels:
                # Check for combined collinearity and proximity
                if are_extremities_compatible(start_dir1, end_dir1, start_dir2, end_dir2, points1[0], points1[-1], points2[0], points2[-1], proximity_threshold):
                    clusters_to_merge.append((label1, label2))
                    merged_labels.add(label1)
                    merged_labels.add(label2)

    # Merge identified clusters
    for label1, label2 in clusters_to_merge:
        filtered_data[label1].extend(filtered_data[label2])
        del filtered_data[label2]

    # Visualization of the New Groups
    # plot_merged_clusters(filtered_data)

    maxDistance = 0.00025
    processedPoints = set()
    boundaries = {}
    lanes = {}

    # Main Loop
    for groupA, points in filtered_data.items():
        for indexA, pointA in enumerate(points):
            # if tuple(pointA) in processedPoints:
            #     continue

            potentialMatches = findClosestPoints(pointA, groupA, filtered_data, maxDistance)

            if len(potentialMatches) == 0:
                raise Exception(f"No potential matches found for point: {pointA}")

            bestScore = {'total':-np.inf, 'distance': np.inf, 'parallelism': -np.inf}
            matchedPoint = None
            matchedGroup = None

            matchedPoint2 = None
            matchedGroupMulti = None

            directionA = calculateDirection(points, indexA)

            for pointB in potentialMatches:
                for groupB, groupPoints in filtered_data.items():
                    if pointB in groupPoints:
                        indexB = groupPoints.index(pointB)
                        directionB = calculateDirection(groupPoints, indexB)
                        break

                distance = evaluateDistance(pointA, pointB)
                parallelism = evaluateParallelism(directionA, directionB)
                score = evaluateScore(distance, parallelism, maxDistance)

                if (abs(distance-bestScore['distance']) < 0.00002) and (abs(parallelism-bestScore['parallelism']) < 0.01) and (matchedGroup is not None) and (groupB != matchedGroup):
                    # print('found double lane point:', bestScore)
                    matchedGroupMulti = [min(matchedGroup, groupB), groupA, max(matchedGroup, groupB)]
                elif score > bestScore['total']:
                    bestScore = {'total':score, 'distance': distance, 'parallelism': parallelism}
                    matchedGroup = groupB


            if matchedGroup is not None:
                addToBoundaries(groupA, pointA, matchedGroup, matchedGroupMulti, boundaries, lanes)
    
    return boundaries, lanes
