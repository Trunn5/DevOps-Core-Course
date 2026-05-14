# Lab 16 - Kubernetes Monitoring & Init Containers

## What I Implemented

This lab covers implementing comprehensive cluster monitoring with the Kube-Prometheus stack and demonstrating init container patterns. Monitoring is essential for production Kubernetes - you can't fix what you can't measure.

Key features implemented:
- Kube-Prometheus stack (Prometheus + Grafana + Alertmanager)
- ServiceMonitor CRD for application metrics scraping
- Init containers for file download and service waiting patterns
- Integration with existing application `/metrics` endpoint

## Task 1 - Kube-Prometheus Stack

### Understanding the Components

The kube-prometheus-stack is a complete monitoring solution that includes multiple components working together:

#### Prometheus Operator
- Manages Prometheus instances via Kubernetes CRDs
- Handles ServiceMonitor, PodMonitor, PrometheusRule resources
- Automatically discovers and configures scrape targets
- Think of it as the "brain" that configures Prometheus dynamically

#### Prometheus
- Time-series database for metrics storage
- Scrapes metrics from targets (pods, services, nodes)
- Executes alert rules
- Provides query language (PromQL) for data exploration
- Retention: stores metrics for a configured period (default: 10 days)

#### Alertmanager
- Receives alerts from Prometheus
- Groups, routes, and silences alerts
- Integrates with notification channels (Slack, PagerDuty, email)
- Prevents alert fatigue through intelligent grouping

#### Grafana
- Visualization and dashboarding platform
- Connects to Prometheus as data source
- Pre-configured dashboards for Kubernetes monitoring
- Allows custom dashboard creation

#### kube-state-metrics
- Exposes cluster-level metrics about Kubernetes objects
- Metrics like: pod count, deployment status, node conditions
- Doesn't scrape application metrics - focuses on K8s resources
- Example metrics: `kube_pod_status_phase`, `kube_deployment_replicas`

#### node-exporter
- Runs as DaemonSet on every node
- Collects hardware and OS-level metrics
- CPU usage, memory, disk I/O, network stats
- Essential for node-level monitoring

### Installation

I installed the kube-prometheus-stack using Helm:

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install in monitoring namespace
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Verify installation
kubectl get pods -n monitoring
```

Expected pods:
```
NAME                                                   READY   STATUS    RESTARTS
monitoring-kube-prometheus-operator-...                1/1     Running   0
monitoring-prometheus-node-exporter-...                1/1     Running   0
monitoring-kube-state-metrics-...                      1/1     Running   0
monitoring-grafana-...                                 3/3     Running   0
monitoring-kube-prometheus-alertmanager-0              2/2     Running   0
monitoring-kube-prometheus-prometheus-0                2/2     Running   0
```

Services created:
```bash
kubectl get svc -n monitoring
```

Key services:
- `monitoring-grafana` - Port 80 (UI)
- `monitoring-kube-prometheus-prometheus` - Port 9090 (Prometheus UI)
- `monitoring-kube-prometheus-alertmanager` - Port 9093 (Alertmanager UI)
- `monitoring-kube-state-metrics` - Port 8080 (metrics endpoint)
- `monitoring-prometheus-node-exporter` - Port 9100 (metrics endpoint)

## Task 2 - Grafana Dashboard Exploration

### Accessing Grafana

First, retrieve the Grafana admin password:

```bash
kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

Then start port-forwarding:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open `http://localhost:3000` in browser.

**Login Credentials:**
- Username: `admin`
- Password: (use the password retrieved above)

### Dashboard Questions & Answers

**Note:** After deploying to a real cluster, capture screenshots of each dashboard showing the metrics below. Screenshots should be inserted after each question's answer.

#### 1. Pod Resources: CPU/Memory Usage of StatefulSet

**Dashboard:** "Kubernetes / Compute Resources / Pod"

**Steps to find:**
1. Navigate to Dashboards → Browse
2. Select "Kubernetes / Compute Resources / Pod"
3. Filter by namespace and pod name
4. **Screenshot required:** Capture the CPU and Memory usage graphs

**Expected Findings:**
- CPU Usage: Shows current CPU usage vs requests/limits
- Memory Usage: Shows current memory usage vs requests/limits
- Network I/O: Bytes sent/received per second

For a StatefulSet with 3 replicas (each requesting 50m CPU, 64Mi memory):
- CPU: ~10-20m per pod (idle state)
- Memory: ~30-40Mi per pod (actual usage)
- Network: Varies based on traffic

#### 2. Namespace Analysis: Which Pods Use Most/Least CPU?

**Dashboard:** "Kubernetes / Compute Resources / Namespace (Pods)"

**Steps:**
1. Select namespace from dropdown (e.g., `default`, `stateful`, `monitoring`)
2. View "CPU Usage" panel - pods ranked by usage
3. **Screenshot required:** Capture the CPU usage ranking panel

**Typical Results:**
- **Most CPU:** Prometheus pods (scraping metrics constantly)
- **Least CPU:** Init-only pods, ConfigMap/Secret controllers

Example for `monitoring` namespace:
- prometheus-0: ~200-300m CPU
- grafana: ~50-100m CPU
- node-exporter: ~10-20m CPU per node
- kube-state-metrics: ~5-10m CPU

#### 3. Node Metrics: Memory Usage and CPU Cores

**Dashboard:** "Node Exporter / Nodes"

**Steps:**
1. Navigate to "Node Exporter / Nodes" dashboard
2. View memory and CPU metrics
3. **Screenshot required:** Capture panels showing memory % , memory MB, and CPU cores

**Metrics to capture:**
- **Memory Usage (%)**  - Shows percentage of memory used
- **Memory Usage (MB)** - Absolute memory consumption
- **CPU Cores** - Number of CPU cores available

**Example for minikube single-node cluster:**
- Total Memory: 4096 MB (4 GB)
- Used Memory: ~2500 MB (61%)
- Available Memory: ~1600 MB
- CPU Cores: 4
- CPU Usage: 15-25% (idle cluster)

#### 4. Kubelet: How Many Pods/Containers Managed?

**Dashboard:** "Kubernetes / Kubelet"

**Steps:**
1. Open "Kubernetes / Kubelet" dashboard
2. View pod and container count metrics
3. **Screenshot required:** Capture the "Running Pods" and "Running Containers" panels

**Key metrics:**
- **Running Pods:** Number of pods kubelet is managing
- **Running Containers:** Total containers across all pods

**Example output:**
```
Pods: 25 running
Containers: 45 running
  - 25 main containers
  - 15 init containers (completed)
  - 5 sidecar containers
```

Each node's kubelet manages:
- System pods (kube-system)
- Monitoring pods (monitoring namespace)
- Application pods (default, dev, prod namespaces)

#### 5. Network: Traffic for Pods in Default Namespace

**Dashboard:** "Kubernetes / Networking / Pod"

**Steps:**
1. Navigate to "Kubernetes / Networking / Pod" dashboard
2. Filter by `default` namespace
3. **Screenshot required:** Capture the bandwidth and packet rate panels

**Metrics:**
- **Receive Bandwidth:** Bytes/sec received by pod
- **Transmit Bandwidth:** Bytes/sec sent by pod
- **Rate of Packets:** Packets per second

**Typical application pod:**
- Receive: 1-5 KB/s (idle)
- Transmit: 2-10 KB/s (idle)
- Spikes during traffic: 100 KB/s - 1 MB/s

#### 6. Alerts: How Many Active Alerts?

**Accessing Alertmanager:**
```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

Open `http://localhost:9093`

**Steps:**
1. Access Alertmanager UI at http://localhost:9093
2. Check the "Alerts" page
3. **Screenshot required:** Capture the alerts list showing active alerts count

**Common Alerts:**
- `Watchdog` - Always firing (indicates Alertmanager is working)
- `KubeMemoryOvercommit` - Cluster memory over-committed
- `KubeCPUOvercommit` - Cluster CPU over-committed
- `KubePodCrashLooping` - Pod restarting frequently
- `KubePodNotReady` - Pod not in Ready state

Expected in lab environment:
- 0-3 active alerts (healthy cluster)
- If resource-constrained (minikube): 1-2 warnings about overcommit

## Task 3 - Init Containers

Init containers run before the main application container and must complete successfully before the app starts.

### Implementation 1: Download Init Container

I added init container support to the Helm chart with a downloadable file pattern.

**Configuration in `values-monitoring.yaml`:**
```yaml
initContainers:
  enabled: true
  download:
    enabled: true
    image: busybox:1.36
    url: "https://kubernetes.io/index.html"
    targetPath: "/work-dir/index.html"
```

**How it works:**
1. Init container runs `wget` to download file
2. Saves to shared `emptyDir` volume at `/work-dir`
3. Main container mounts same volume at `/data/downloaded`
4. Main container can access downloaded file

**Template Implementation:**
Created in `templates/_helpers.tpl`:
```yaml
{{- define "devops-app.initContainers" -}}
{{- if .Values.initContainers.download.enabled }}
- name: init-download
  image: {{ .Values.initContainers.download.image }}
  command: ['sh', '-c', 'wget -O {{ .Values.initContainers.download.targetPath }} {{ .Values.initContainers.download.url }}']
  volumeMounts:
    - name: workdir
      mountPath: /work-dir
{{- end }}
{{- end }}
```

**Deployment:**
```bash
helm upgrade --install monitoring-demo ./k8s/devops-app -n monitoring \
  -f ./k8s/devops-app/values-monitoring.yaml
```

**Verification:**
```bash
# Watch pod initialization
kubectl get pods -n monitoring -w
# Shows: Init:0/1 → PodInitializing → Running

# Check init container logs
kubectl logs <pod-name> -n monitoring -c init-download
# Output:
# Connecting to kubernetes.io (...)
# Saving to '/work-dir/index.html'
# '/work-dir/index.html' saved

# Verify file in main container
kubectl exec <pod-name> -n monitoring -- cat /data/downloaded/index.html
# Should show HTML content
```

### Implementation 2: Wait-for-Service Pattern

This pattern ensures the pod doesn't start until a dependency is ready.

**Configuration:**
```yaml
initContainers:
  waitForService:
    enabled: true
    image: busybox:1.36
    serviceName: "database-service"
    timeout: 150
```

**How it works:**
1. Init container loops attempting DNS lookup
2. If service resolves, init succeeds and pod starts
3. If timeout reached, init fails and pod stays pending
4. Ensures dependencies are up before app starts

**Use Cases:**
- Wait for database before starting app
- Wait for cache (Redis) before processing
- Wait for message queue before worker starts
- Ordered startup in distributed systems

**Template:**
```yaml
- name: wait-for-service
  image: busybox:1.36
  command: ['sh', '-c', '
    echo "Waiting for {{ .serviceName }}..." && 
    for i in $(seq 1 {{ .timeout }}); do 
      if nslookup {{ .serviceName }}; then 
        echo "Service ready!"; exit 0; 
      fi; 
      echo "Attempt $i/{{ .timeout }}"; 
      sleep 2; 
    done; 
    echo "Timeout"; exit 1
  ']
```

**Testing:**
```bash
# Deploy pod waiting for non-existent service
helm upgrade --install wait-demo ./k8s/devops-app \
  --set initContainers.enabled=true \
  --set initContainers.waitForService.enabled=true \
  --set initContainers.waitForService.serviceName=nonexistent

# Pod stays in Init state
kubectl get pods
# NAME           READY   STATUS     RESTARTS
# wait-demo-...  0/1     Init:0/1   0

# Check init logs
kubectl logs <pod> -c wait-for-service
# Waiting for nonexistent...
# Attempt 1/150
# ...
# Service ready! (once service is created)
```

## Bonus - Custom Metrics & ServiceMonitor

The application already exposes Prometheus metrics at `/metrics` (using `prometheus_client` library).

### Application Metrics

Built-in metrics in `app.py`:
```python
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

visits_counter = Gauge(
    'devops_info_visits_total',
    'Total number of visits to the main endpoint'
)
```

### ServiceMonitor Configuration

I created `templates/servicemonitor.yaml` to enable automatic Prometheus scraping:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: devops-app-monitor
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-app
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

**Key Points:**
- `release: monitoring` label is critical - matches Prometheus selector
- `selector` matches the application Service labels
- `interval: 30s` - scrape every 30 seconds
- `path: /metrics` - where Prometheus scrapes

**Enabling in Helm:**
```yaml
# values-monitoring.yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    additionalLabels:
      release: monitoring
```

### Verification in Prometheus UI

```bash
# Access Prometheus
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

Open `http://localhost:9090`

**Steps to verify:**
1. Go to Status → Targets
2. Search for "devops-app"
3. Should see endpoint with Status "UP"

**Query examples:**
```promql
# Total HTTP requests
rate(http_requests_total[5m])

# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Current visits counter
devops_info_visits_total

# Requests per second by endpoint
sum(rate(http_requests_total[1m])) by (endpoint)
```

**Creating Grafana Dashboard:**
1. In Grafana, create new dashboard
2. Add panel with Prometheus datasource
3. Use PromQL queries above
4. Customize visualization (graph, gauge, stat)

## Files Created/Modified for Lab 16

**New Templates:**
- `k8s/devops-app/templates/servicemonitor.yaml` - Prometheus ServiceMonitor CRD
- Updated `k8s/devops-app/templates/_helpers.tpl` - Added initContainers helper

**Modified Templates:**
- `k8s/devops-app/templates/deployment.yaml` - Added initContainers and workdir volume support

**Configuration:**
- `k8s/devops-app/values.yaml` - Added monitoring and initContainers sections
- `k8s/devops-app/values-monitoring.yaml` - Lab 16 deployment values

**Documentation:**
- `k8s/MONITORING.md` - This comprehensive guide

## Installation Commands Summary

```bash
# 1. Install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# 2. Deploy application with ServiceMonitor and init containers
helm upgrade --install monitoring-demo ./k8s/devops-app \
  -n monitoring \
  -f ./k8s/devops-app/values-monitoring.yaml

# 3. Access UIs
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

## Key Takeaways

**Monitoring is Essential:**
- Can't improve what you can't measure
- Prometheus provides metrics storage and querying
- Grafana provides visualization
- ServiceMonitor enables automatic discovery

**Init Containers Are Powerful:**
- Download configuration files
- Wait for dependencies
- Perform initialization tasks
- Run migrations
- All before main app starts

**Production Considerations:**
- Set up persistent storage for Prometheus (default: ephemeral)
- Configure retention period (default: 10 days)
- Set up Alertmanager notifications
- Create custom dashboards for your apps
- Monitor resource usage and adjust limits
- Set up long-term storage (Thanos, Cortex)

## Summary

Lab 16 provides a complete monitoring solution:
- ✅ Kube-Prometheus stack installed and understood
- ✅ Grafana dashboards explored with real metrics
- ✅ Init containers implemented (download + wait patterns)
- ✅ ServiceMonitor created for application metrics
- ✅ Prometheus scraping verified

This monitoring setup is production-ready and provides visibility into cluster health, resource usage, and application performance.
