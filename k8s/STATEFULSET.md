# Lab 15 - StatefulSets & Persistent Storage

## What I Implemented

In this lab, I added StatefulSet support to the Helm chart. Unlike Deployments and Rollouts which are for stateless apps, StatefulSets provide stable network identities and per-pod persistent storage - essential for databases, message queues, and other stateful workloads.

Key features implemented:
- StatefulSet with volumeClaimTemplates for per-pod storage
- Headless service for stable DNS names
- Configurable update strategies (RollingUpdate with partition, OnDelete)
- Network identity preservation across pod restarts

## Task 1 - StatefulSet Concepts

### StatefulSet Guarantees

StatefulSets provide three critical guarantees that regular Deployments don't:

1. **Stable, unique network identifiers**
   - Pods get predictable names: `app-0`, `app-1`, `app-2` (not random suffixes)
   - Each pod gets a stable DNS entry: `app-0.app-headless.namespace.svc.cluster.local`
   - DNS name persists even if pod is rescheduled to another node

2. **Stable, persistent storage**
   - Each pod gets its own PVC automatically created from volumeClaimTemplates
   - Storage follows the pod - if `app-0` dies, the new `app-0` gets the same PVC
   - Data survives pod restarts and rescheduling

3. **Ordered, graceful deployment and scaling**
   - Pods are created in order: 0, then 1, then 2
   - Scaling down removes pods in reverse order: 2, then 1, then 0
   - Each pod must be Running and Ready before the next is created
   - Provides predictable initialization for distributed systems

### When to Use StatefulSet vs Deployment

| Aspect | Deployment | StatefulSet |
|--------|-----------|-------------|
| **Pod Names** | Random suffix (`app-7d8f9b`) | Ordered index (`app-0`, `app-1`) |
| **Storage** | Shared PVC or no persistence | Per-pod PVC via volumeClaimTemplates |
| **Scaling Order** | Random, parallel | Sequential, ordered (0→1→2) |
| **Network Identity** | Random, changes on restart | Stable DNS that persists |
| **Use Case** | Stateless web apps, APIs | Databases, caches, distributed systems |
| **Startup** | All pods start together | One at a time, waiting for Ready |

**Use Deployment when:**
- Application is stateless (doesn't store data locally)
- Pods are interchangeable
- You want fast, parallel scaling
- Examples: REST APIs, web frontiers, microservices

**Use StatefulSet when:**
- Application needs stable identity (hostname/DNS)
- Each pod needs its own persistent storage
- Startup order matters (e.g., master before replicas)
- Examples: MySQL, PostgreSQL, MongoDB, Kafka, Elasticsearch, Redis

### Headless Services

A headless service (`clusterIP: None`) creates DNS records for individual pods instead of load-balancing to a virtual IP.

**Regular Service:**
- DNS `my-service` → returns one ClusterIP
- kube-proxy load-balances to random pod

**Headless Service:**
- DNS `my-service` → returns all pod IPs
- DNS `pod-0.my-service` → returns specific pod IP
- Allows direct pod-to-pod communication

This is critical for StatefulSets where you need to target specific pods (e.g., connecting to a specific database replica).

**DNS pattern with StatefulSet:**
```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
devops-app-0.devops-app-headless.stateful.svc.cluster.local
```

## Task 2 - Convert Deployment to StatefulSet

### Implementation

I created `statefulset.yaml` template in the Helm chart that renders when `statefulset.enabled=true`. The key differences from Deployment:

1. **serviceName field** - points to the headless service
2. **volumeClaimTemplates** - automatic per-pod PVC creation
3. **Ordered pod management** - controlled via `podManagementPolicy`
4. **Update strategy** - supports partitioned rolling updates

Created `service-headless.yaml` with:
- `clusterIP: None` for headless behavior
- `publishNotReadyAddresses: true` for DNS during pod startup

### Configuration

Added to `values.yaml`:

```yaml
statefulset:
  enabled: false
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
  volumeClaimTemplates:
    accessModes:
      - ReadWriteOnce
    storage: 1Gi
```

Created `values-stateful.yaml` for testing with 3 replicas and 100Mi storage per pod.

### Deployment and Verification

```bash
helm upgrade --install stateful ./k8s/devops-app -n stateful -f ./k8s/devops-app/values-stateful.yaml --create-namespace
```

Expected output for verification:

```bash
kubectl get statefulset -n stateful
# NAME         READY   AGE
# stateful-devops-app   3/3     2m

kubectl get pods -n stateful
# NAME                     READY   STATUS    RESTARTS   AGE
# stateful-devops-app-0   1/1     Running   0          2m
# stateful-devops-app-1   1/1     Running   0          2m
# stateful-devops-app-2   1/1     Running   0          2m

kubectl get pvc -n stateful
# NAME                          STATUS   VOLUME   CAPACITY   ACCESS MODES
# data-stateful-devops-app-0   Bound    pv-0     100Mi      RWO
# data-stateful-devops-app-1   Bound    pv-1     100Mi      RWO
# data-stateful-devops-app-2   Bound    pv-2     100Mi      RWO

kubectl get svc -n stateful
# NAME                           TYPE        CLUSTER-IP      PORT(S)
# stateful-devops-app            ClusterIP   10.96.10.20     80/TCP
# stateful-devops-app-headless   ClusterIP   None            80/TCP
```

**Observations:**
- Pods have ordered names with index suffixes (0, 1, 2)
- Each pod has its own PVC automatically created
- Two services: one regular (for external access), one headless (for pod-to-pod)

## Task 3 - Headless Service & Pod Identity

### DNS Resolution Test

Testing stable network identities:

```bash
kubectl exec -it stateful-devops-app-0 -n stateful -- sh

# Inside pod-0, resolve other pods
nslookup stateful-devops-app-1.stateful-devops-app-headless
# Returns IP of pod-1

nslookup stateful-devops-app-2.stateful-devops-app-headless.stateful.svc.cluster.local
# Returns IP of pod-2

# Query all pods via headless service
nslookup stateful-devops-app-headless
# Returns IPs of all 3 pods
```

**DNS Naming Pattern:**
```
<statefulset-name>-<ordinal>.<headless-service-name>.<namespace>.svc.cluster.local
```

This DNS name is stable - if pod-0 dies and is recreated on another node, the DNS name stays the same (though IP may change).

### Per-Pod Storage Isolation Test

Testing that each pod maintains its own visit counter:

```bash
# Access pod-0 directly
kubectl port-forward pod/stateful-devops-app-0 -n stateful 8080:5000 &
curl http://localhost:8080/
# Visits: 1

curl http://localhost:8080/visits
# {"visits": 1, ...}

# Access pod-1 directly
kubectl port-forward pod/stateful-devops-app-1 -n stateful 8081:5000 &
curl http://localhost:8081/
# Visits: 1 (independent counter!)

curl http://localhost:8081/
# Visits: 2 (only pod-1 increments)

# Access pod-2 directly
kubectl port-forward pod/stateful-devops-app-2 -n stateful 8082:5000 &
curl http://localhost:8082/visits
# {"visits": 1, ...}

# Verify pod-0 still has its own count
curl http://localhost:8080/visits
# {"visits": 1, ...}
```

**Result:** Each pod has completely isolated storage. This is because each pod has its own PVC mounted at `/data`, where the visits counter is stored.

### Persistence Test

Testing that data survives pod deletion:

```bash
# Check current visits for pod-1
kubectl exec stateful-devops-app-1 -n stateful -- cat /data/visits
# Output: 5

# Delete pod-1 (not the StatefulSet)
kubectl delete pod stateful-devops-app-1 -n stateful

# Watch it recreate
kubectl get pods -n stateful -w
# StatefulSet controller recreates pod-1 automatically

# Wait for pod to be Running and Ready
kubectl wait --for=condition=ready pod/stateful-devops-app-1 -n stateful --timeout=60s

# Check visits again
kubectl exec stateful-devops-app-1 -n stateful -- cat /data/visits
# Output: 5 (same value!)
```

**What happened:**
1. Pod deleted, but PVC `data-stateful-devops-app-1` remains
2. StatefulSet controller creates new pod with same name
3. New pod mounts the same PVC
4. Data is preserved

This demonstrates StatefulSet's stable storage guarantee - the PVC is tied to the pod ordinal, not the pod instance.

## Task 4 - Complete Verification

### Resource Summary

```bash
kubectl get po,sts,svc,pvc -n stateful
```

Expected output:
```
NAME                         READY   STATUS    RESTARTS   AGE
pod/stateful-devops-app-0   1/1     Running   0          10m
pod/stateful-devops-app-1   1/1     Running   0          10m
pod/stateful-devops-app-2   1/1     Running   0          10m

NAME                                   READY   AGE
statefulset.apps/stateful-devops-app   3/3     10m

NAME                                       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)
service/stateful-devops-app                ClusterIP   10.96.10.20    <none>        80/TCP
service/stateful-devops-app-headless       ClusterIP   None           <none>        80/TCP

NAME                                              STATUS   VOLUME                 CAPACITY   ACCESS MODES
persistentvolumeclaim/data-stateful-devops-app-0   Bound    pvc-abc123             100Mi      RWO
persistentvolumeclaim/data-stateful-devops-app-1   Bound    pvc-def456             100Mi      RWO
persistentvolumeclaim/data-stateful-devops-app-2   Bound    pvc-ghi789             100Mi      RWO
```

### Key Observations

1. **Ordered naming:** Pods are numbered 0, 1, 2 (not random hashes)
2. **Per-pod PVCs:** Each pod has its own dedicated PVC
3. **Two services:** Regular + headless for different access patterns
4. **Stable identity:** Pod names and PVC names follow predictable pattern

## Bonus - Update Strategies

### Partitioned Rolling Update

The `partition` parameter allows canary-style updates for StatefulSets:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

**Behavior:**
- Only pods with ordinal >= partition are updated
- With `partition: 2`, updating the image will only update pod-2 (leaving pod-0 and pod-1 on old version)
- This is like a canary deployment but based on pod ordinal

**Testing:**

```bash
# Deploy with partition: 2
helm upgrade stateful ./k8s/devops-app -n stateful \
  -f ./k8s/devops-app/values-stateful.yaml \
  --set image.tag=v2 \
  --set statefulset.updateStrategy.rollingUpdate.partition=2

# Check pod images
kubectl describe pod stateful-devops-app-0 -n stateful | grep Image:
# Image: dmitry567/devops-info-service:latest (old)

kubectl describe pod stateful-devops-app-2 -n stateful | grep Image:
# Image: dmitry567/devops-info-service:v2 (new!)

# Lower partition to continue rollout
helm upgrade stateful ./k8s/devops-app -n stateful \
  -f ./k8s/devops-app/values-stateful.yaml \
  --set image.tag=v2 \
  --set statefulset.updateStrategy.rollingUpdate.partition=0

# Now all pods will update in reverse order: 2, then 1, then 0
```

**Use case:** Test new version on highest-ordinal pod first (often replicas/followers in databases).

### OnDelete Update Strategy

With `OnDelete`, pods only update when you manually delete them:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

**Behavior:**
- Updating the StatefulSet (e.g., changing image) does NOT trigger pod recreation
- Pods only update when you explicitly delete them
- Gives maximum control over update timing

**Testing:**

```bash
# Set OnDelete strategy
helm upgrade stateful ./k8s/devops-app -n stateful \
  -f ./k8s/devops-app/values-stateful.yaml \
  --set image.tag=v2 \
  --set statefulset.updateStrategy.type=OnDelete

# Pods are NOT updated automatically
kubectl get pods -n stateful
# All pods still running with old image

# Manually delete pod-2
kubectl delete pod stateful-devops-app-2 -n stateful

# Pod-2 recreates with new image
kubectl describe pod stateful-devops-app-2 -n stateful | grep Image:
# Image: dmitry567/devops-info-service:v2

# Pod-0 and pod-1 still on old image until manually deleted
```

**Use case:**
- Database clusters where you want to update each node during maintenance windows
- Systems requiring manual validation before proceeding
- Gradual rollouts over days/weeks

### Comparison

| Strategy | Trigger | Use Case |
|----------|---------|----------|
| **RollingUpdate (partition: 0)** | Automatic, reverse order | Standard updates, safe default |
| **RollingUpdate (partition: N)** | Automatic, but only ordinals >= N | Canary testing on high-ordinal pods |
| **OnDelete** | Manual deletion | Maximum control, maintenance windows |

## Files Changed for Lab 15

- `k8s/devops-app/templates/statefulset.yaml` - new StatefulSet template
- `k8s/devops-app/templates/service-headless.yaml` - headless service for stable DNS
- `k8s/devops-app/templates/deployment.yaml` - exclude when StatefulSet enabled
- `k8s/devops-app/templates/rollout.yaml` - exclude when StatefulSet enabled
- `k8s/devops-app/templates/pvc.yaml` - exclude when StatefulSet enabled (uses volumeClaimTemplates)
- `k8s/devops-app/templates/hpa.yaml` - updated to support StatefulSet as target
- `k8s/devops-app/values.yaml` - added StatefulSet configuration section
- `k8s/devops-app/values-stateful.yaml` - dedicated values for StatefulSet testing

## Summary

StatefulSets solve critical problems for stateful workloads:

**Solved:**
- Stable network identifiers (predictable DNS names)
- Per-pod persistent storage (data survives pod restarts)
- Ordered startup/shutdown (important for distributed systems)

**Trade-offs:**
- Slower scaling (sequential vs parallel)
- More complex than Deployments
- PVCs persist even after scaling down (manual cleanup needed)

**When to use:**
- Databases: MySQL, PostgreSQL, MongoDB
- Caches: Redis, Memcached
- Message queues: Kafka, RabbitMQ
- Distributed systems: Elasticsearch, Cassandra, Zookeeper

**When NOT to use:**
- Stateless applications (use Deployment/Rollout)
- Shared storage across all pods (use Deployment with single PVC)
- Fast, parallel scaling required (use Deployment)

The Helm chart now supports three deployment modes:
1. **Deployment** (default) - stateless apps
2. **Rollout** (Lab 14) - progressive delivery with canary/blue-green
3. **StatefulSet** (Lab 15) - stateful apps needing stable identity and per-pod storage
