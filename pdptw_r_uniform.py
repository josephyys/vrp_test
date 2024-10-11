import time
import random
from networkx import DiGraph, relabel_nodes, set_node_attributes
from numpy import array
import networkx as nx
from vrpy import VehicleRoutingProblem
import matplotlib.pyplot as plt

# Number of pairs (pickup and delivery)
PAIRS = 40

# # Start timer
# start_time = time.time()

# Randomly generate distances (between 10 and 1000 units)
DISTANCES = [[0 if i == j else random.randint(10, 1000) for j in range(PAIRS + 2)] for i in range(PAIRS + 2)]

# Randomly generate demands (pickup positive, delivery negative)
DEMAND = {i: random.randint(1, 5) if i % 2 == 1 else -random.randint(1, 5) for i in range(1, PAIRS + 1)}

# Create the graph G from the distance matrix
A = array(DISTANCES, dtype=[("cost", int)])
G = nx.from_numpy_array(A, create_using=nx.DiGraph())



# The depot is relabeled as Source and Sink
G = relabel_nodes(G, {0: "Source", PAIRS + 1: "Sink"})


# Set node attributes (demands)
set_node_attributes(G, values=DEMAND, name="demand")

# Function to assign time windows between 8:00 AM and 6:00 PM
def assign_time_windows(G, pairs):
    start_of_day = 8 * 60 * 60  # 8:00 AM in seconds
    end_of_day = 18 * 60 * 60   # 6:00 PM in seconds

    time_windows_lower = {}
    time_windows_upper = {}

    for i in range(1, pairs + 1):
        lower_bound = random.randint(start_of_day, end_of_day - 3600)  # Latest start is 5:00 PM (to leave room for duration)
        duration = random.randint(1200, 3600)  # Between 20 minutes and 1 hour (in seconds)
        upper_bound = min(lower_bound + duration, end_of_day)  # Ensure the end is within the day
        time_windows_lower[i] = lower_bound
        time_windows_upper[i] = upper_bound

    # Set time window attributes to the graph
    nx.set_node_attributes(G, time_windows_lower, "lower")
    nx.set_node_attributes(G, time_windows_upper, "upper")

# Assign time windows
assign_time_windows(G, PAIRS)

# Drawing function to visualize the graph with time windows
def draw_graph_with_time_windows(G):
    pos = nx.spring_layout(G)  # Use spring layout for better node placement
    plt.figure(figsize=(10, 8))
    
    # Draw nodes and labels
    nx.draw_networkx_nodes(G, pos, node_size=600, node_color='lightblue')
    nx.draw_networkx_labels(G, pos, labels={i: f"{i}" for i in G.nodes})
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrowstyle='->', arrowsize=20, edge_color='gray')
    
    # Annotate time windows on nodes
    for node, (x, y) in pos.items():
        lower = G.nodes[node].get("lower")
        upper = G.nodes[node].get("upper")
        if lower and upper:
            lower_time = f"{lower // 3600}:{(lower % 3600) // 60:02d}"  # Convert from seconds to HH:MM
            upper_time = f"{upper // 3600}:{(upper % 3600) // 60:02d}"
            plt.text(x, y - 0.1, f"{lower_time}-{upper_time}", fontsize=8, ha='center')
    
    plt.title("Graph with Time Windows (8:00 AM to 6:00 PM)")
    plt.grid(True)
    plt.show()

# Visualize the graph with the assigned time windows
draw_graph_with_time_windows(G)

# # End timer
# end_time = time.time()

# # Output results
# print(f"Time taken: {end_time - start_time} seconds")

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

# Start timer
start_time = time.time()

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
macbook

windows 89:
10: 2 sec
20: 33 sec
30: 194 sec -> 3 min 14 sec
'''