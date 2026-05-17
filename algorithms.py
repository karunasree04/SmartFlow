import heapq

# ─────────────────────────────────────────
#  PRIORITY QUEUE (MAX-HEAP)
# ─────────────────────────────────────────
def calculate_priority(lane_counts):
    return [(count * 10, i) for i, count in enumerate(lane_counts)]

def priority_queue(priorities):
    pq = []
    for p, lane in priorities:
        heapq.heappush(pq, (-p, lane))
    return pq

def get_highest_priority(pq):
    return heapq.heappop(pq)

def calculate_green_time(vehicle_count, min_time=15, max_time=90):
    """Calculate green signal duration based on vehicle count."""
    time = min_time + (vehicle_count * 3)
    return min(time, max_time)

# ─────────────────────────────────────────
#  DIJKSTRA — GOOGLE MAPS STYLE
# ─────────────────────────────────────────

# Road network: nodes = intersections, edges = roads with distance + congestion
ROAD_NETWORK = {
    'nodes': {
        'A': {'label': 'Main Gate',        'x': 100, 'y': 300},
        'B': {'label': 'City Center',      'x': 300, 'y': 150},
        'C': {'label': 'Hospital',         'x': 500, 'y': 100},
        'D': {'label': 'Market Junction',  'x': 300, 'y': 300},
        'E': {'label': 'College Road',     'x': 500, 'y': 300},
        'F': {'label': 'Bus Stand',        'x': 700, 'y': 200},
        'G': {'label': 'Railway Station',  'x': 700, 'y': 400},
        'H': {'label': 'Airport Road',     'x': 900, 'y': 300},
    },
    'edges': [
        ('A', 'B', 4),
        ('A', 'D', 3),
        ('B', 'C', 5),
        ('B', 'D', 2),
        ('B', 'F', 8),
        ('C', 'F', 4),
        ('D', 'E', 6),
        ('E', 'F', 3),
        ('E', 'G', 5),
        ('F', 'H', 4),
        ('G', 'H', 3),
    ]
}

def build_graph(edges, congestion=None):
    """Build adjacency list. Congestion adds extra weight (simulates traffic)."""
    graph = {}
    for u, v, w in edges:
        extra = 0
        if congestion:
            extra = congestion.get((u,v), congestion.get((v,u), 0))
        if u not in graph: graph[u] = {}
        if v not in graph: graph[v] = {}
        graph[u][v] = w + extra
        graph[v][u] = w + extra
    return graph

def dijkstra_path(graph, start, end):
    """
    Dijkstra's algorithm — returns shortest distance AND full path.
    Uses min-heap for O((V+E) log V) efficiency.
    """
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0
    heap = [(0, start)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u].items():
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    # Reconstruct path
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    if path[0] != start:
        return float('inf'), []   # no path found

    return dist[end], path

def get_all_paths_info(start, end, lane_counts=None):
    """
    Returns:
      - shortest path (distance only)
      - smart path (distance + traffic congestion weight)
      - full node/edge data for visualization
    """
    edges  = ROAD_NETWORK['edges']
    nodes  = ROAD_NETWORK['nodes']

    # Build normal graph
    normal_graph = build_graph(edges)

    # Build congested graph — heavy lanes add cost to certain roads
    congestion = {}
    if lane_counts:
        max_c = max(lane_counts) if max(lane_counts) > 0 else 1
        # Map lane congestion to road segments
        mapping = [('A','D'), ('D','E'), ('E','G'), ('G','H')]
        for i, seg in enumerate(mapping):
            if i < len(lane_counts):
                extra = int((lane_counts[i] / max_c) * 10)
                congestion[seg] = extra

    smart_graph = build_graph(edges, congestion)

    short_dist, short_path = dijkstra_path(normal_graph, start, end)
    smart_dist, smart_path = dijkstra_path(smart_graph,  start, end)

    return {
        'nodes'      : nodes,
        'edges'      : edges,
        'short_dist' : short_dist,
        'short_path' : short_path,
        'smart_dist' : smart_dist,
        'smart_path' : smart_path,
        'congestion' : congestion,
        'start'      : start,
        'end'        : end,
    }
