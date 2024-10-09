from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from ortools.constraint_solver.pywrapcp import RoutingModel, RoutingIndexManager

# Helper function to print the solution
def print_solution(manager, routing, solution):
    """Print the solution."""
    print(f'Objective: {solution.ObjectiveValue()}')
    max_route_distance = 0
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route.append(manager.IndexToNode(index))
        print(f'Route for vehicle {vehicle_id}: {route}')
        print(f'Distance of the route: {route_distance}m')
        max_route_distance = max(route_distance, max_route_distance)
    print(f'Maximum of the route distances: {max_route_distance}m')

# Distance matrix
DISTANCES = [
[0,548,776,696,582,274,502,194,308,194,536,502,388,354,468,776,662,0], # from Source
[0,0,684,308,194,502,730,354,696,742,1084,594,480,674,1016,868,1210,548],
[0,684,0,992,878,502,274,810,468,742,400,1278,1164,1130,788,1552,754,776],
[0,308,992,0,114,650,878,502,844,890,1232,514,628,822,1164,560,1358,696],
[0,194,878,114,0,536,764,388,730,776,1118,400,514,708,1050,674,1244,582],
[0,502,502,650,536,0,228,308,194,240,582,776,662,628,514,1050,708,274],
[0,730,274,878,764,228,0,536,194,468,354,1004,890,856,514,1278,480,502],
[0,354,810,502,388,308,536,0,342,388,730,468,354,320,662,742,856,194],
[0,696,468,844,730,194,194,342,0,274,388,810,696,662,320,1084,514,308],
[0,742,742,890,776,240,468,388,274,0,342,536,422,388,274,810,468,194],
[0,1084,400,1232,1118,582,354,730,388,342,0,878,764,730,388,1152,354,536],
[0,594,1278,514,400,776,1004,468,810,536,878,0,114,308,650,274,844,502],
[0,480,1164,628,514,662,890,354,696,422,764,114,0,194,536,388,730,388],
[0,674,1130,822,708,628,856,320,662,388,730,308,194,0,342,422,536,354],
[0,1016,788,1164,1050,514,514,662,320,274,388,650,536,342,0,764,194,468],
[0,868,1552,560,674,1050,1278,742,1084,810,1152,274,388,422,764,0,798,776],
[0,1210,754,1358,1244,708,480,856,514,468,354,844,730,536,194,798,0,662],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], # from Sink
]

# Demands (key: node, value: amount)
DEMAND = {1: 1, 2: 2, 3: 3, 4: -3, 5: 1, 6: -1, 7: 2, 8: -2, 9: -1, 10: -2, 11: -3, 12: -1, 13: 1, 14: 4, 15: 3, 16: -4}

# pickups_deliveries = {(1, 6): 1, (2, 10): 2, (4, 3): 3, (5, 9): 1, (7, 8): 2, (15, 11): 3, (13, 12): 1, (16, 14): 4}
pickups_deliveries = {(6,1): 1, (2, 10): 2, (4, 3): 3, (9, 5): 1, (7, 8): 2, (15, 11): 3, (12, 13): 1, (14, 16): 4}

# Create routing index manager
start_depots = [0, 0, 0]  # All vehicles start at node 0 (source)
end_depots = [1, 1, 1]    # All vehicles end at node 1 (sink)
# manager = RoutingIndexManager(len(DISTANCES), 3, start_depots, end_depots)
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from ortools.constraint_solver.pywrapcp import RoutingModel, RoutingIndexManager

# Create routing index manager with separate start and end depots for each vehicle
manager = RoutingIndexManager(len(DISTANCES), 3, [0, 0, 0], [1, 1, 1])

# Create Routing Model
routing = RoutingModel(manager)

# Define cost of each arc
def distance_callback(from_index, to_index):
    """Returns the distance between the two nodes."""
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return DISTANCES[from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)

# Set the cost of travel between nodes
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Add Capacity constraint
demand_evaluator_index = routing.RegisterUnaryTransitCallback(lambda idx: DEMAND[manager.IndexToNode(idx)])
routing.AddDimensionWithVehicleCapacity(
    demand_evaluator_index,
    0,  # null capacity slack
    [4] * 3,  # vehicle maximum capacities
    True,  # start cumul to zero
    "Capacity")

# Define Pickup and Delivery pairs
for pickup, delivery in pickups_deliveries:
    pickup_index = manager.NodeToIndex(pickup)
    delivery_index = manager.NodeToIndex(delivery)
    routing.AddPickupAndDelivery(pickup_index, delivery_index)
    routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))

# Add Time limit and Search Parameters
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.time_limit.seconds = 10  # Set a 10-second time limit

# Solve the problem
solution = routing.SolveWithParameters(search_parameters)

# If a solution exists, print it
if solution:
    print_solution(manager, routing, solution)
else:
    print('No solution found within the time limit.')
