from networkx import DiGraph, relabel_nodes, set_node_attributes
from numpy import array
import networkx  as nx

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
# DEMAND = {1: 1, 2: 1, 3: 2, 4: 4, 5: 2, 6: 4, 7: 8, 8: 8, 9: 1, 10: 2, 11: 1, 12: 2, 13: 4, 14: 4, 15: 8, 16: 8}
DEMAND = {1: 1, 2: 2, 3: 3, 4: -3, 5: 1, 6: -1, 7: 2, 8: -2, 9: -1, 10: -2, 11: -3, 12: -1, 13: 1, 14: 4, 15: 3, 16: -4}


# The matrix is transformed into a DiGraph
A = array(DISTANCES, dtype=[("cost", int)])
G = nx.from_numpy_array(A, create_using=nx.DiGraph())

# The demands are stored as node attributes
set_node_attributes(G, values=DEMAND, name="demand")

# The depot is relabeled as Source and Sink
G = relabel_nodes(G, {0: "Source", 17: "Sink"})


pickups_deliveries = {(1, 6): 1, (2, 10): 2, (4, 3): 3, (5, 9): 1, (7, 8): 2, (15, 11): 3, (13, 12): 1, (16, 14): 4}
for (u, v) in pickups_deliveries:
    G.nodes[u]["request"] = v
    # Pickups are accounted for positively
    G.nodes[u]["demand"] = pickups_deliveries[(u, v)]
    # Deliveries are accounted for negatively
    G.nodes[v]["demand"] = -pickups_deliveries[(u, v)]


from vrpy import VehicleRoutingProblem
prob = VehicleRoutingProblem(G, load_capacity=16, num_stops=16, pickup_delivery=True)
prob.solve(cspy=False)
print(prob.best_value)
print(prob.best_routes)
print(prob.node_load)


# {1: ['Source', 5, 2, 10, 16, 14, 9, 'Sink'], 2: ['Source', 13, 15, 11, 12, 'Sink'], 3: ['Source', 7, 4, 3, 1, 6, 8, 'Sink']}
# {1: {'Source': 0, 5: 1, 2: 3, 10: 1, 16: 5, 14: 1, 9: 0, 'Sink': 0}, 2: {'Source': 0, 13: 1, 15: 4, 11: 1, 12: 0, 'Sink': 0}, 3: {'Source': 0, 7: 2, 4: 5, 3: 2, 1: 3, 6: 2, 8: 0, 'Sink': 0}}
# (pdp) (base) joseph@j2022-macbook VRP % touch pdpt