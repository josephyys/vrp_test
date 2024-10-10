import time
import random
from networkx import DiGraph, relabel_nodes, set_node_attributes
from numpy import array
import networkx as nx
from vrpy import VehicleRoutingProblem

# Number of pairs (pickup and delivery)
PAIRS = 50

# Start timer
start_time = time.time()

# Randomly generate distances (between 10 and 1000 units)
DISTANCES = [[0 if i == j else random.randint(10, 1000) for j in range(PAIRS + 2)] for i in range(PAIRS + 2)]

# Randomly generate demands (pickup positive, delivery negative)
DEMAND = {i: random.randint(1, 5) if i % 2 == 1 else -random.randint(1, 5) for i in range(1, PAIRS + 1)}

# Create the graph G from the distance matrix
A = array(DISTANCES, dtype=[("cost", int)])
G = nx.from_numpy_array(A, create_using=nx.DiGraph())

# The depot is relabeled as Source and Sink
G = relabel_nodes(G, {0: "Source", PAIRS + 1: "Sink"})

# Randomly generate time windows for the nodes
TIME_WINDOWS_LOWER = {i: random.randint(0, 10) for i in range(1, PAIRS + 1)}
TIME_WINDOWS_UPPER = {i: TIME_WINDOWS_LOWER[i] + random.randint(5, 10) for i in range(1, PAIRS + 1)}

# Set node attributes (demands and time windows)
set_node_attributes(G, values=DEMAND, name="demand")
set_node_attributes(G, values=TIME_WINDOWS_LOWER, name="lower")
set_node_attributes(G, values=TIME_WINDOWS_UPPER, name="upper")

# Generate random pairs (u, v) for pickups and deliveries
pickups_deliveries = {(2*i+1, 2*i+2): DEMAND[2*i+1] for i in range(PAIRS // 2)}

# Assign pickup and delivery attributes
for (u, v) in pickups_deliveries:
    G.nodes[u]["request"] = v
    G.nodes[u]["demand"] = pickups_deliveries[(u, v)]
    G.nodes[v]["demand"] = -pickups_deliveries[(u, v)]

# Ensure the source node has no incoming edges
for u in list(G.predecessors("Source")):
    G.remove_edge(u, "Source")

# Ensure the sink node has no outgoing edges
for v in list(G.successors("Sink")):
    G.remove_edge("Sink", v)

# Now proceed with the VRP setup
time_limit = 60*60*3
prob = VehicleRoutingProblem(G, load_capacity=5, num_stops=6, pickup_delivery=True)
prob.solve(cspy=False, ) #time_limit=time_limit

# End timer
end_time = time.time()

# Output results
print(f"Best objective value: {prob.best_value}")
print(f"Best routes: {prob.best_routes}")
print(f"Node loads: {prob.node_load}")
print(f"Time taken: {end_time - start_time} seconds")

def check_pairs_served(routing, manager, solution, data):
    served_pairs = set()
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            for pickup, delivery in data['pickups_deliveries']:
                if node_index == pickup:
                    served_pairs.add((pickup, delivery))
            index = solution.Value(routing.NextVar(index))

    total_pairs = set(data['pickups_deliveries'])  # Your original pairs
    missing_pairs = total_pairs - served_pairs

    if missing_pairs:
        print(f"Missing pairs in the solution: {missing_pairs}")
    else:
        print("All pairs are served in the solution.")


'''
10: 6 sec
20: 203 sec -> 3 min 23 sec
30: 970 sec -> 16 min 10 sec
40: 2003 sec -> 33 min 23 sec, 3600+ sec,
50:  10800+ sec -> 3 hr+
100:

'''