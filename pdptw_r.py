import time
import random
from networkx import DiGraph, relabel_nodes, set_node_attributes
from numpy import array
import networkx as nx
from vrpy import VehicleRoutingProblem

# Number of pairs (pickup and delivery)
PAIRS = 100

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
prob = VehicleRoutingProblem(G, load_capacity=5, num_stops=6, pickup_delivery=True)
prob.solve(cspy=False)

# End timer
end_time = time.time()

# Output results
print(f"Best objective value: {prob.best_value}")
print(f"Best routes: {prob.best_routes}")
print(f"Node loads: {prob.node_load}")
print(f"Time taken: {end_time - start_time} seconds")

'''
10: 6 sec
100:

'''