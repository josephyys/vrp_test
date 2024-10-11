import time
import random
import networkx as nx
from numpy import array
from vrpy import VehicleRoutingProblem
import matplotlib.pyplot as plt

# Number of pairs (pickup and delivery)
PAIRS = 10

# Randomly generate distances (between 10 and 1000 units)
DISTANCES = [[0 if i == j else random.randint(10, 1000) for j in range(PAIRS + 2)] for i in range(PAIRS + 2)]

# Randomly generate demands (pickup positive, delivery negative)
DEMAND = {i: random.randint(1, 5) if i % 2 == 1 else -random.randint(1, 5) for i in range(1, PAIRS + 1)}

# Create the graph G from the distance matrix
A = array(DISTANCES, dtype=[("cost", int)])
G = nx.from_numpy_array(A, create_using=nx.DiGraph())

# Relabel Source and Sink
G = nx.relabel_nodes(G, {0: "Source", PAIRS + 1: "Sink"})

# Set node attributes (demands)
nx.set_node_attributes(G, values=DEMAND, name="demand")

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


# Function to assign time windows divided into hourly intervals
def assign_time_windows(G, pairs):
    start_of_day = 8 * 60 * 60  # 8:00 AM in seconds
    end_of_day = 18 * 60 * 60   # 6:00 PM in seconds

    time_windows_lower = {}
    time_windows_upper = {}

    for i in range(1, pairs + 1):
        lower_bound = random.randint(start_of_day, end_of_day - 3600)  # Latest start at 5:00 PM
        duration = random.randint(1200, 3600)  # Between 20 minutes and 1 hour
        upper_bound = min(lower_bound + duration, end_of_day)  # Ensure the end is within the day
        time_windows_lower[i] = lower_bound
        time_windows_upper[i] = upper_bound

    # Set time window attributes to the graph
    nx.set_node_attributes(G, time_windows_lower, "lower")
    nx.set_node_attributes(G, time_windows_upper, "upper")

# Assign time windows
assign_time_windows(G, PAIRS)

# Set pickup and delivery requests using old code
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

# Define hourly zones and solve VRP for each hour sequentially
def solve_hour_zones(G, num_hours=10):
    start_of_day = 8 * 60 * 60  # 8:00 AM in seconds
    hour_duration = 3600  # 1 hour in seconds
    total_elapsed_time = 0

    preassigned_routes = []  # Holds the routes from previous hour
    preassigned_nodes = set()  # Keeps track of nodes already processed

    for hour in range(num_hours):
        print(f"\nSolving for Hour {hour + 1} ({start_of_day // 3600 + hour}:00 to {start_of_day // 3600 + hour + 1}:00)")

        # Define time window for this hour
        lower_bound = start_of_day + hour * hour_duration
        upper_bound = start_of_day + (hour + 1) * hour_duration

        # Initialize lists for pickups and deliveries
        pickups = []
        deliveries = []

        # Separate pickups and deliveries based on nodes in the graph
        for n in G.nodes:
            demand = G.nodes[n].get("demand", 0)
            if demand > 0:
                # If demand is positive, it's a pickup
                pickups.append(n)
            elif demand < 0:
                # If demand is negative, it's a delivery
                deliveries.append(n)

        # Print all pickup and delivery nodes
        print(f"Pickup nodes: {pickups}")
        print(f"Delivery nodes: {deliveries}")

        # Generate valid requests based on pickups and deliveries in the current hour
        valid_requests = []
        
        # Collect all pairs of pickups and deliveries
        for pickup in pickups:
            if (G.nodes[pickup]["lower"] <= upper_bound and G.nodes[pickup]["upper"] >= lower_bound):
                for delivery in deliveries:
                    if (G.nodes[delivery]["lower"] <= upper_bound and G.nodes[delivery]["upper"] >= lower_bound):
                        valid_requests.append((pickup, delivery))
        
        # Print all generated valid pairs before filtering
        print(f"All potential pickup-delivery pairs for Hour {hour + 1}: {valid_requests}")

        # Check for valid requests in this hour
        if not valid_requests:
            print(f"Skipping Hour {hour + 1}: No valid pickup-delivery pairs.")
            continue

        # Create subgraph for the nodes in this hour
        subG = G.subgraph(set(pickups + deliveries) | {"Source", "Sink"}).copy()

        # Ensure Source has no incoming edges and Sink has no outgoing edges
        for u in list(subG.predecessors("Source")):
            subG.remove_edge(u, "Source")
        for v in list(subG.successors("Sink")):
            subG.remove_edge("Sink", v)

        # Check and ensure demand does not exceed capacity
        total_demand = sum(G.nodes[u]["demand"] for u in pickups + deliveries if u in subG)
        if total_demand > 5:  # Adjust this based on your vehicle's capacity
            print(f"Skipping Hour {hour + 1}: Total demand {total_demand} exceeds vehicle capacity.")
            continue

        # Print the current subgraph's nodes and edges for debugging
        print(f"Nodes in subgraph for Hour {hour + 1}: {subG.nodes()}")
        print(f"Edges in subgraph for Hour {hour + 1}: {subG.edges()}")

        # Solve the VRP for this subgraph
        start_time = time.time()
        prob = VehicleRoutingProblem(subG, load_capacity=5, num_stops=6, pickup_delivery=True)

        try:
            prob.solve(cspy=False)
        except Exception as e:
            print(f"Error solving for Hour {hour + 1}: {e}")
            continue

        end_time = time.time()

        elapsed_time = end_time - start_time
        total_elapsed_time += elapsed_time

        # Output results for this hour
        print(f"Hour {hour + 1} solution:")
        print(f"Best objective value: {prob.best_value}")
        print(f"Best routes: {prob.best_routes}")
        print(f"Node loads: {prob.node_load}")
        print(f"Time taken for Hour {hour + 1}: {elapsed_time} seconds")

        # Update preassigned routes for the next hour
        preassigned_routes = []
        if prob.best_routes:
            for route in prob.best_routes.values():
                if len(route) > 1:
                    preassigned_routes.append(route)
                    preassigned_nodes.update(route[:-1])

        # Draw the graph for the current hour zone
        draw_graph_with_time_windows(subG)

    # Output the total time taken
    print(f"\nTotal time taken for all hours: {total_elapsed_time} seconds")

# Solve VRP for each hourly zone
solve_hour_zones(G, num_hours=10)
