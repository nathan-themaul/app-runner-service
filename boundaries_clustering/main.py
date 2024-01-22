import sys
from clustering import get_clustering
from boundaries import sort_all_boundaries
from smoothing import smooth_boundaries
from centerlines import calculate_centerlines, prepare_endpoints, create_nodes_from_endpoints
from plotting import plot_lanes, plot_lanes_with_smoothed_lines, plot_lanes_with_centerlines
from database import get_dataset
import numpy as np
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.int64):
            return int(obj)
        # Add more customizations if necessary for other types
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Convert ndarray to list
        return json.JSONEncoder.default(self, obj)

def dev_execution():
    # main execution logic
    # input_data = json.loads(sys.argv[1])
    boundaries, lanes = get_clustering()

    sorted_boundaries = sort_all_boundaries(boundaries)
    # plot_lanes(boundaries)

    smoothed_boundaries = smooth_boundaries(sorted_boundaries, 'opti_spline')
    calculate_centerlines(smoothed_boundaries, lanes)
    endpoints = prepare_endpoints(lanes)
    nodes = create_nodes_from_endpoints(endpoints)
    # link_centerlines_to_central_nodes(lanes, nodes)


    plot_lanes_with_smoothed_lines(smoothed_boundaries, lanes, nodes)



    # final_lanes = find_centerlines_for_lanes(smoothed_boundaries)

    # plot_lanes_with_centerlines(final_lanes)

    # Convert tuple keys to strings
    converted_points = {str(key): value for key, value in smoothed_boundaries.items()}

    # Serialize with json.dumps
    # json_str = json.dumps(converted_points, cls=CustomJSONEncoder)
    # print(json_str)

def process_data(stage, data=None, method=None):
    if stage == 'initialisation':
        dataset = get_dataset()
        return json.dumps({"points": dataset}, cls=CustomJSONEncoder)
    if stage == 'clustering':
        clusters, lanes = get_clustering()
        boundaries = sort_all_boundaries(clusters)
        return json.dumps({"boundaries": boundaries, "lanes": lanes}, cls=CustomJSONEncoder)

    elif stage == 'smoothing':
        if data is not None:
            boundaries = data
        return json.dumps({"smoothed_boundaries": smooth_boundaries(boundaries, method)}, cls=CustomJSONEncoder)

    elif stage == 'centerlines':
        if data is not None:
            boundaries = data.get('boundaries')
            lanes = data.get('lanes')
        return json.dumps({"updated_lanes": calculate_centerlines(boundaries, lanes, method)}, cls=CustomJSONEncoder)
    
    elif stage == 'all':
        boundaries, lanes = get_clustering()
        sorted_boundaries = sort_all_boundaries(boundaries)
        smoothed_boundaries = smooth_boundaries(sorted_boundaries, 'opti_spline')
        converted_points = {str(key): value for key, value in smoothed_boundaries.items()}
        return json.dumps(converted_points, cls=CustomJSONEncoder)

    return json.dumps({"error": "Invalid stage specified"}, cls=CustomJSONEncoder)


if __name__ == "__main__":
    stage = sys.argv[1]

    if stage == 'dev':
        dev_execution()
    else:
        # Read from stdin
        input_str = sys.stdin.read()
        input_data = json.loads(input_str) if input_str else {}
        method = input_data.get('method')
        data = input_data.get('data')

        print(process_data(stage, data, method))