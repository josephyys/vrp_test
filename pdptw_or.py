from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
import random
import time

# Configuration
PAIRS = 10  # Number of pickup and delivery pairs
VEHICLE_CAPACITY = 4
NUM_VEHICLES = 6
DEPOT = 0

def create_data_model():
    """Stores the data for the problem."""
    data = {}
    # Distance matrix (randomly generated)
    data['distance_matrix'] = np.random.randint(100, 1000, size=(PAIRS * 2 + 1, PAIRS * 2 + 1)).tolist()

    # Randomly generated demands and time windows
    data['demands'] = [0] + [random.randint(1, VEHICLE_CAPACITY) for _ in range(PAIRS)] + [-random.randint(1, VEHICLE_CAPACITY) for _ in range(PAIRS)]
    data['time_windows'] = [(0, 500)] + [(random.randint(0, 50), random.randint(60, 100)) for _ in range(PAIRS)] * 2
    data['vehicle_capacities'] = [VEHICLE_CAPACITY] * NUM_VEHICLES
    data['num_vehicles'] = NUM_VEHICLES
    data['depot'] = DEPOT
    data['pickups_deliveries'] = [(i + 1, i + PAIRS + 1) for i in range(PAIRS)]
    return data

def solve_vrp():
    """Solve the VRP with pickup and delivery using OR-Tools."""
    start_time = time.time()

    # Create the data model
    data = create_data_model()

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback (distance function)
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Set cost function (minimize distance)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Retrieve the capacity dimension to use its cumul vars
    capacity_dimension = routing.GetDimensionOrDie('Capacity')

    # Define Pickup and Delivery pairs and enforce capacity constraints
    for pickup, delivery in data['pickups_deliveries']:
        pickup_index = manager.NodeToIndex(pickup)
        delivery_index = manager.NodeToIndex(delivery)
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))

        # Enforce that the capacity (cumulative load) at the pickup point is positive
        capacity_dimension.CumulVar(pickup_index).SetRange(0, VEHICLE_CAPACITY)
        capacity_dimension.CumulVar(delivery_index).SetRange(0, VEHICLE_CAPACITY)

    # Setting search parameters with relaxation options
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    # Heuristic to generate the initial solution
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)

    # Time limit for search
    search_parameters.time_limit.seconds = 30  # Increased time limit

    # Solution limit
    search_parameters.solution_limit = 500

    # Enable local search strategies
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)

    search_parameters.log_search = True  # To get insights into search progress

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution
    if solution:
        print(f"Solution found in {time.time() - start_time} seconds.")
        print_solution(manager, routing, solution, data)
    else:
        print("No solution found! Could not retrieve any partial solution.")

def print_solution(manager, routing, solution, data):
    """Prints the solution to the console."""
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index), route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))

if __name__ == '__main__':
    solve_vrp()
