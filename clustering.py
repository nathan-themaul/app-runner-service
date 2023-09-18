import sys
import json
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import LineString, Point, mapping
from collections import defaultdict

def segment_line(line, max_distance):
        segments = []
        points = list(line.coords)
        current_segment = [points[0]]

        for point in points[1:]:
            if Point(point).distance(Point(current_segment[-1])) > max_distance:
                if len(current_segment) > 1: # Check if the current_segment has more than one point
                    segments.append(LineString(current_segment))
                current_segment = [point]
            else:
                current_segment.append(point)
        
        if len(current_segment) > 1: # Check if the last segment has more than one point
            segments.append(LineString(current_segment))
        return segments

def angle_between_lines(line1, line2):
        # Extract the coordinates of the two points defining the first line.
        x1, y1 = line1.coords[0]
        x2, y2 = line1.coords[1]

        # Extract the coordinates of the two points defining the second line.
        x3, y3 = line2.coords[0]
        x4, y4 = line2.coords[1]

        # Calculate the angles for each line segment with respect to the x-axis.
        angle1 = np.arctan2(y2 - y1, x2 - x1)
        angle2 = np.arctan2(y4 - y3, x4 - x3)
        
        # Return the absolute difference of angles in degrees.
        return np.abs((angle1 - angle2) * 180 / np.pi)

def split_lines_at_change_of_road(lines, angle_threshold):
        new_lines = []  # This will store the split lines.

        # Iterate through each line in the provided list.
        for line in lines:
            # Break down the line into a list of consecutive pairs of coordinates.
            segments = list(zip(line.coords[:-1], line.coords[1:]))

            current_line = [segments[0][0]]
            cumulative_angle = 0.0
            prev_angle = 0.0
            
            # Iterate through each segment of the line, comparing it to the next one.
            for i, (segment1, segment2) in enumerate(zip(segments[:-1], segments[1:])):
                # Create LineString objects from the segments to pass to the angle calculation function.
                line1 = LineString(segment1)
                line2 = LineString(segment2)

                # Calculate the angle between the two consecutive line segments.
                angle = angle_between_lines(line1, line2)
                if angle * prev_angle >= 0:  # The line is turning in the same direction
                    cumulative_angle += angle
                else:  # The line is turning in the opposite direction, so we reset the angle
                    cumulative_angle = angle
                prev_angle = angle
                if abs(cumulative_angle) > angle_threshold:  # The line has turned enough to split it
                    if len(current_line) > 1:  # Only add to new_lines if there are at least 2 points
                        new_lines.append(LineString(current_line))
                    current_line = [segments[i][1]]  # Start the new line at the end of the current segment
                    cumulative_angle = 0.0
                # Extend the current line segment.
                current_line.append(segment2[1])
            if len(current_line) > 1:  # Only add to new_lines if there are at least 2 points
                new_lines.append(LineString(current_line))
        return new_lines

def get_direction_vector(line):
        """Get the representative vector of the line from the first quarter to the third quarter."""
        coords = list(line.coords)
        idx_25 = len(coords) // 4
        idx_75 = 3 * len(coords) // 4
        v = np.array(coords[idx_75]) - np.array(coords[idx_25])
        return v / np.linalg.norm(v)

def can_merge(line1, line2, distance_threshold=5.0, angle_threshold=30):
    # Proximity checks
    start_to_end = LineString([line1.coords[0], line2.coords[-1]]).length < distance_threshold
    end_to_start = LineString([line1.coords[-1], line2.coords[0]]).length < distance_threshold
    
    if not (start_to_end or end_to_start):
        return False
    
    v1 = get_direction_vector(line1)
    v2 = get_direction_vector(line2)
    angle = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0)) * (180/np.pi)
    
    # If lines are almost perpendicular, no merge
    if 80 < angle < 100:
        return False
    
    # If lines are not moving in the same general direction, no merge
    if angle > angle_threshold and angle < 180 - angle_threshold:
        return False
    
    return True


def can_merge_by_endpoints(line1, line2, distance_threshold=5.0):
    """Check if two lines can be merged based on their endpoints."""
    start_to_end = LineString([line1.coords[0], line2.coords[-1]]).length < distance_threshold
    start_to_start = LineString([line1.coords[0], line2.coords[0]]).length < distance_threshold
    end_to_start = LineString([line1.coords[-1], line2.coords[0]]).length < distance_threshold
    end_to_end = LineString([line1.coords[-1], line2.coords[-1]]).length < distance_threshold

    return start_to_end or end_to_start or start_to_start or end_to_end


class UnionFind:
    def __init__(self, n):
        self.parent = [i for i in range(n)]
        self.rank = [0] * n
        
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return
        
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        else:
            self.parent[root_y] = root_x
            if self.rank[root_x] == self.rank[root_y]:
                self.rank[root_x] += 1

def get_grouping(lines, distance_threshold=0.0002, angle_threshold=35):
    """Group lines based on direction and proximity."""
    uf = UnionFind(len(lines))
    
    for i, line1 in enumerate(lines):
        for j, line2 in enumerate(lines):
            if j <= i:
                continue
            if can_merge(line1, line2, distance_threshold, angle_threshold):
                uf.union(i, j)
                
    return [uf.find(i) for i in range(len(lines))]

def refine_groups(lines, groups):
    """Refine groups to ensure no group contains more than 2 parallel lines."""
    group_contents = defaultdict(list)
    
    # Associate each line with its group
    for idx, group in enumerate(groups):
        group_contents[group].append(lines[idx])

    refined_groups = {}  # new group id -> list of lines
    new_group_id = 0

    # Refine each group
    for group, lines_in_group in group_contents.items():
        if len(lines_in_group) <= 2:
            refined_groups[new_group_id] = lines_in_group
            new_group_id += 1
        else:
            # Overlapping lines based on their endpoints can be merged without limits
            # but more than 2 parallel lines should be split.
            while len(lines_in_group) > 0:
                line = lines_in_group.pop(0)
                parallel_lines = [line]
                
                i = 0
                while i < len(lines_in_group):
                    if are_almost_parallel(line, lines_in_group[i]):
                        parallel_lines.append(lines_in_group.pop(i))
                    else:
                        i += 1
                
                refined_groups[new_group_id] = parallel_lines
                new_group_id += 1

    # Create new group labels
    new_groups = []
    for line in lines:
        for group_id, lines_in_group in refined_groups.items():
            if line in lines_in_group:
                new_groups.append(group_id)
                break

    return new_groups

def are_almost_parallel(line1, line2, angle_threshold=15):
    """Check if two lines are nearly parallel."""
    v1 = get_direction_vector(line1)
    v2 = get_direction_vector(line2)
    angle = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0)) * (180/np.pi)
    return angle < angle_threshold or angle > 180 - angle_threshold


def get_clustering(points):
    dataset = np.array(points)

    ### PART 2 : cluster using distance between points

    # DBSCAN
    db = DBSCAN(eps=0.000025, min_samples=3).fit(dataset)
    labels = db.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)


    ### PART 3 : separate intersections

    lines = [LineString(dataset[labels == i]) for i in range(n_clusters)]
    intersections = [line1.intersection(line2) for line1 in lines for line2 in lines if line1 != line2 and line1.intersects(line2)]

    for i in range(n_clusters):
        for point in intersections:
            if isinstance(point, Point):
                if point in lines[i]:
                    lines[i] = [p for p in lines[i] if p != point]

    # Set a max distance (you'll need to adjust this based on your data)
    max_distance = 0.0001

    # Segment the lines
    segmented_lines = [segment for line in lines for segment in segment_line(line, max_distance)]


    ### PART 4 : separate curves
    
    # Set an angle threshold
    angle_threshold = 280  # Adjust this value based on your data

    # Split the lines
    lines = split_lines_at_change_of_road(segmented_lines, angle_threshold)

    for line in lines:
        x, y = line.xy


    ### PART 5 : merge lines in same continuity into one boundary

    initial_groups = get_grouping(lines)

    # Refine the groups
    refined_groups = refine_groups(lines, initial_groups)
    return lines

if __name__ == "__main__":
    # Read JSON payload from standard input
    input_json = json.load(sys.stdin)
    points = input_json.get("points", [])
    
    # Perform clustering
    result = get_clustering(points)
    
    # Convert the list of LineString objects to dictionaries
    line_list_dict = [mapping(line) for line in result]
    
    # Serialize the list of dictionaries to a JSON string
    line_list_json = json.dumps(line_list_dict)
    
    # Prepare the output payload
    output = {
        'message': 'Clustering ran successfully',
        'result': line_list_json
    }
    
    # Write JSON output to standard output
    print(json.dumps(output))
