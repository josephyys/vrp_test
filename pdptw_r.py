import time
import random
from networkx import DiGraph, relabel_nodes, set_node_attributes
from numpy import array
import networkx as nx
from vrpy import VehicleRoutingProblem
import random

# PAIRS設定：假設要處理10對pickup-delivery任務
PAIRS = 40

# 生成隨機的距離矩陣，並確保對稱性
DISTANCES = [[0 if i == j else random.randint(10, 1000) for j in range(PAIRS + 2)] for i in range(PAIRS + 2)]
for i in range(len(DISTANCES)):
    for j in range(i, len(DISTANCES)):
        DISTANCES[j][i] = DISTANCES[i][j]  # 確保矩陣對稱

# 將距離矩陣轉換為DiGraph
A = array(DISTANCES, dtype=[("cost", int)])
G = nx.from_numpy_array(A, create_using=nx.DiGraph())

# 重命名depot為Source和Sink
G = relabel_nodes(G, {0: "Source", PAIRS + 1: "Sink"})



# 隨機設定pickup-delivery對應的工作負荷
pickups_deliveries = {(2 * i + 1, 2 * i + 2): random.randint(1, 4) for i in range(PAIRS//2)}

# 載荷需求 pickup 隨機1-4, 對應的 delivery 是對應的負數
DEMAND = {}
for pickup, delivery in pickups_deliveries:
    DEMAND[pickup] = pickups_deliveries[(pickup, delivery)]  # 正數代表取走的載荷
    DEMAND[delivery] = -pickups_deliveries[(pickup, delivery)]  # 負數代表交付的載荷

# 生成時間窗口必須符合 (pickup, delivery)，pickup < delivery
TIME_WINDOWS_LOWER = {}
TIME_WINDOWS_UPPER = {}

for pickup, delivery in pickups_deliveries:
    # 隨機生成時間窗口下限，pickup 必須先於 delivery
    pickup_lower = random.randint(0, 10)
    delivery_lower = pickup_lower + random.randint(1, 5)  # 保證 delivery 晚於 pickup

    TIME_WINDOWS_LOWER[pickup] = pickup_lower
    TIME_WINDOWS_UPPER[pickup] = pickup_lower + random.randint(5, 10)  # 設定pickup的上限
    TIME_WINDOWS_LOWER[delivery] = delivery_lower
    TIME_WINDOWS_UPPER[delivery] = delivery_lower + random.randint(5, 10)  # 設定delivery的上限

# 檢查結果
print("Pickups and Deliveries:", pickups_deliveries)
print("Demands:", DEMAND)
print("Time Windows Lower Bound:", TIME_WINDOWS_LOWER)
print("Time Windows Upper Bound:", TIME_WINDOWS_UPPER)


# 設定節點的屬性（載荷和時間窗口）
set_node_attributes(G, values=DEMAND, name="demand")
set_node_attributes(G, values=TIME_WINDOWS_LOWER, name="lower")
set_node_attributes(G, values=TIME_WINDOWS_UPPER, name="upper")




# print(f"pickups_deliveries: {pickups_deliveries}")
# print(f"TIME_WINDOWS_LOWER: {TIME_WINDOWS_LOWER}")
# print(f"TIME_WINDOWS_UPPER: {TIME_WINDOWS_UPPER}")
# print(f"DEMAND: {DEMAND}")

for (u, v) in pickups_deliveries:
    G.nodes[u]["request"] = v
    G.nodes[u]["demand"] = pickups_deliveries[(u, v)]
    G.nodes[v]["demand"] = -pickups_deliveries[(u, v)]

# 確保Source節點沒有incoming edges，Sink節點沒有outgoing edges
for u in list(G.predecessors("Source")):
    G.remove_edge(u, "Source")

for v in list(G.successors("Sink")):
    G.remove_edge("Sink", v)

# 設定時間窗口限制的檢查
for (u, v) in pickups_deliveries:
    if TIME_WINDOWS_UPPER[u] < TIME_WINDOWS_LOWER[v]:
        print(f"Error: Pickup {u} cannot deliver to {v} due to incompatible time windows.")

start_time = time.time()
# 設置VRP問題
prob = VehicleRoutingProblem(G, load_capacity=5, num_stops=6, pickup_delivery=True)
prob.time_windows = True
prob.solve(cspy=False)  # 設定 time_limit 等其他參數

# 計算完成時間
end_time = time.time()

# 輸出結果
print(f"Best objective value: {prob.best_value}")
print(f"Best routes: {prob.best_routes}")
print(f"Node loads: {prob.node_load}")
# 計算總共花費的秒數
total_time = end_time - start_time

# 將總秒數轉換為小時、分鐘、秒
hours = int(total_time // 3600)
minutes = int((total_time % 3600) // 60)
seconds = int(total_time % 60)

# 構建時間顯示字串，根據是否有小時或分鐘決定是否顯示
time_str = ""
if hours > 0:
    time_str += f"{hours} hr "
if minutes > 0:
    time_str += f"{minutes} min "
time_str += f"{seconds} sec"

# 顯示結果
print(f"Time taken: {time_str}")


