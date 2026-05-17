#include <stdio.h>
#include <limits.h>

#define MAX 100

// ---------------- STRUCT ----------------
typedef struct {
    int priority;
    int lane;
} Node;

// Global heap
Node heap[MAX];
int size = 0;

// ---------------- CALCULATE PRIORITY ----------------
void calculate_priority(int lane_counts[], Node priorities[], int n) {
    for (int i = 0; i < n; i++) {
        priorities[i].priority = lane_counts[i] * 10;
        priorities[i].lane = i;
    }
}

// ---------------- HEAP HELPER FUNCTIONS ----------------
void swap(Node *a, Node *b) {
    Node temp = *a;
    *a = *b;
    *b = temp;
}

void heapify_up(int i) {
    while (i > 0 && heap[(i - 1) / 2].priority < heap[i].priority) {
        swap(&heap[i], &heap[(i - 1) / 2]);
        i = (i - 1) / 2;
    }
}

void heapify_down(int i) {
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;

    if (left < size && heap[left].priority > heap[largest].priority)
        largest = left;

    if (right < size && heap[right].priority > heap[largest].priority)
        largest = right;

    if (largest != i) {
        swap(&heap[i], &heap[largest]);
        heapify_down(largest);
    }
}

// ---------------- PRIORITY QUEUE ----------------
void priority_queue(Node priorities[], int n) {
    size = 0;
    for (int i = 0; i < n; i++) {
        heap[size] = priorities[i];
        size++;
        heapify_up(size - 1);
    }
}

// ---------------- GET HIGHEST PRIORITY ----------------
Node get_highest_priority() {
    Node top = heap[0];
    heap[0] = heap[size - 1];
    size--;
    heapify_down(0);
    return top;
}

// ---------------- DIJKSTRA ----------------
void dijkstra(int graph[MAX][MAX], int n, int start, int dist[]) {
    int visited[MAX] = {0};

    for (int i = 0; i < n; i++)
        dist[i] = INT_MAX;

    dist[start] = 0;

    for (int i = 0; i < n - 1; i++) {
        int min = INT_MAX, u = -1;

        for (int j = 0; j < n; j++) {
            if (!visited[j] && dist[j] < min) {
                min = dist[j];
                u = j;
            }
        }

        if (u == -1) break;

        visited[u] = 1;

        for (int v = 0; v < n; v++) {
            if (!visited[v] && graph[u][v] &&
                dist[u] != INT_MAX &&
                dist[u] + graph[u][v] < dist[v]) {

                dist[v] = dist[u] + graph[u][v];
            }
        }
    }
}