# Lab 9: Kubernetes Fundamentals

## Overview

This lab deploys the DevOps Info Service to Kubernetes using production-ready manifests. It demonstrates container orchestration, scaling, rolling updates, and advanced networking with Ingress and TLS.

## Architecture

```
┌─────────────────────────────────────────────┐
│            Ingress Controller               │
│  (NGINX) - TLS Termination                  │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   /app1           /app2
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│  Python App │  │  Nginx App  │
│  Service    │  │  Service    │
└──────┬──────┘  └──────┬──────┘
       │                │
   ┌───┴────┬────┐  ┌──┴───┐
   │        │    │  │      │
  Pod1   Pod2  Pod3 Pod1  Pod2
  (3 replicas)     (2 replicas)
```

## Prerequisites

### Tools Installation

You need to install:
1. **kubectl** - Kubernetes CLI
2. **minikube** OR **kind** - Local Kubernetes cluster

**Install kubectl (macOS):**
```bash
brew install kubectl
```

**Install minikube (macOS):**
```bash
brew install minikube
```

**OR Install kind (macOS):**
```bash
brew install kind
```

## Task 1: Local Kubernetes Setup (2 pts)

### Cluster Setup

**Using minikube:**
```bash
# Start cluster
minikube start --driver=docker --memory=4096 --cpus=2

# Verify cluster
kubectl cluster-info
kubectl get nodes
kubectl version --short
```

**Using kind:**
```bash
# Create cluster
kind create cluster --name devops-lab9

# Verify cluster
kubectl cluster-info --context kind-devops-lab9
kubectl get nodes
```

### Expected Output

**`kubectl cluster-info`:**
```
Kubernetes control plane is running at https://127.0.0.1:xxxxx
CoreDNS is running at https://127.0.0.1:xxxxx/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

**`kubectl get nodes`:**
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   10m   v1.33.0
```

### Why Minikube?

Minikube is recommended for this lab because:
- Full-featured local Kubernetes environment
- Built-in addons (ingress, metrics-server, dashboard)
- Easy service access with `minikube service`
- Better documentation and community support
- Simpler networking for Ingress

## Task 2: Application Deployment (3 pts)

### Deployment Manifest

**File:** `k8s/deployment.yml`

**Key Features:**
- **3 replicas** for high availability
- **Rolling update strategy** for zero-downtime deployments
- **Resource limits** to prevent resource starvation
- **Health probes** for self-healing
- **Security context** for non-root execution

**Resource Configuration:**
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

**Health Checks:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

### Deployment Commands

```bash
# Create namespace
kubectl apply -f k8s/namespace.yml

# Deploy application
kubectl apply -f k8s/deployment.yml

# Check deployment status
kubectl get deployments -n devops
kubectl get pods -n devops
kubectl describe deployment devops-python-app -n devops

# Check pod details
kubectl get pods -n devops -o wide
kubectl logs -n devops -l app=devops-python --tail=50
```

### Expected Output

```
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-python-app    3/3     3            3           2m

NAME                                  READY   STATUS    RESTARTS   AGE
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

## Task 3: Service Configuration (2 pts)

### Service Manifest

**File:** `k8s/service.yml`

**Configuration:**
- **Type:** ClusterIP (will use Ingress for external access)
- **Selector:** `app: devops-python` (matches Deployment labels)
- **Port:** 80 (service port) → 5000 (container port)

### Service Commands

```bash
# Apply service
kubectl apply -f k8s/service.yml

# Check service
kubectl get services -n devops
kubectl describe service devops-python-service -n devops

# Test service internally (port-forward)
kubectl port-forward -n devops service/devops-python-service 8080:80

# In another terminal:
curl http://localhost:8080/
curl http://localhost:8080/health
```

### Service Discovery

Pods can reach the service at:
- `devops-python-service.devops.svc.cluster.local:80`
- `devops-python-service.devops:80`
- `devops-python-service:80` (from same namespace)

## Task 4: Scaling and Updates (2 pts)

### Scaling Operations

**Scale to 5 replicas:**
```bash
# Declarative approach (preferred)
kubectl scale deployment devops-python-app -n devops --replicas=5

# Verify scaling
kubectl get pods -n devops -w

# Check replica count
kubectl get deployment devops-python-app -n devops
```

**Expected output:**
```
NAME                                  READY   STATUS    RESTARTS   AGE
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          10s
devops-python-app-xxxxxxxxxx-xxxxx   1/1     Running   0          10s
```

### Rolling Update

**Update image tag:**
```bash
# Update to a new version (or same image with latest tag)
kubectl set image deployment/devops-python-app \
  devops-python=dmitry567/devops-info-service:latest \
  -n devops

# Watch the rollout
kubectl rollout status deployment/devops-python-app -n devops

# Check rollout history
kubectl rollout history deployment/devops-python-app -n devops
```

**Observe rolling update:**
```bash
# Watch pods being replaced one by one
kubectl get pods -n devops -w
```

### Rollback

**If update fails, rollback:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/devops-python-app -n devops

# Rollback to specific revision
kubectl rollout undo deployment/devops-python-app -n devops --to-revision=1

# Check rollout history
kubectl rollout history deployment/devops-python-app -n devops
```

### Zero Downtime Verification

During rolling update, verify service remains available:
```bash
# In one terminal, watch rollout
kubectl rollout status deployment/devops-python-app -n devops

# In another terminal, continuously test service
while true; do curl -s http://localhost:8080/health | jq .status; sleep 1; done
```

## Bonus Task: Ingress with TLS (2.5 pts)

### Setup Ingress Controller

**For minikube:**
```bash
# Enable ingress addon
minikube addons enable ingress

# Verify ingress controller
kubectl get pods -n ingress-nginx
```

**For kind:**
```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Deploy Second Application

```bash
# Deploy nginx app
kubectl apply -f k8s/deployment-nginx.yml
kubectl apply -f k8s/service-nginx.yml

# Verify both apps running
kubectl get deployments -n devops
kubectl get services -n devops
```

### Generate TLS Certificate

```bash
cd k8s

# Run certificate generation script
./generate-tls.sh

# Create Kubernetes secret
kubectl create secret tls devops-tls-secret \
  --key tls.key \
  --cert tls.crt \
  -n devops

# Verify secret
kubectl get secrets -n devops
kubectl describe secret devops-tls-secret -n devops
```

### Deploy Ingress

```bash
# Apply Ingress manifest
kubectl apply -f k8s/ingress.yml

# Check Ingress status
kubectl get ingress -n devops
kubectl describe ingress devops-apps-ingress -n devops
```

### Configure Local DNS

**Add to `/etc/hosts`:**
```bash
# Get minikube IP
minikube ip

# Add entry (replace <MINIKUBE_IP> with actual IP)
sudo sh -c "echo '<MINIKUBE_IP> devops.local' >> /etc/hosts"

# Verify
cat /etc/hosts | grep devops.local
```

**For kind:**
```bash
# kind uses localhost
sudo sh -c "echo '127.0.0.1 devops.local' >> /etc/hosts"
```

### Test Ingress Routing

**HTTP (redirects to HTTPS):**
```bash
curl -L http://devops.local/app1
curl -L http://devops.local/app2
```

**HTTPS with self-signed cert:**
```bash
# Python app
curl -k https://devops.local/app1
curl -k https://devops.local/app1/health

# Nginx app
curl -k https://devops.local/app2
```

**In browser:**
1. Visit https://devops.local/app1 (accept security warning)
2. Visit https://devops.local/app2
3. Verify both apps are accessible

### Ingress Benefits

**vs NodePort Services:**
- ✅ Single entry point for multiple services
- ✅ Path-based routing (one domain, many apps)
- ✅ TLS termination at edge
- ✅ Better resource usage (one load balancer)
- ✅ HTTP-level routing (headers, methods, etc.)

## ConfigMap Usage

### Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yml
```

### Update Deployment to Use ConfigMap

Update `deployment.yml` to use ConfigMap for environment variables:

```yaml
env:
- name: PORT
  valueFrom:
    configMapKeyRef:
      name: devops-python-config
      key: PORT
- name: ENVIRONMENT
  valueFrom:
    configMapKeyRef:
      name: devops-python-config
      key: ENVIRONMENT
```

## Verification Checklist

### Task 1: Setup
- [ ] kubectl installed and configured
- [ ] Local cluster running (minikube/kind)
- [ ] Cluster info shows control plane running
- [ ] Node shows Ready status

### Task 2: Deployment
- [ ] Deployment created with 3 replicas
- [ ] All pods in Running state
- [ ] Health probes configured
- [ ] Resource limits set
- [ ] Security context configured

### Task 3: Service
- [ ] Service created and active
- [ ] Service accessible via port-forward
- [ ] All endpoints responding correctly

### Task 4: Scaling & Updates
- [ ] Successfully scaled to 5 replicas
- [ ] Rolling update completed without errors
- [ ] Rollback demonstrated
- [ ] Zero downtime verified

### Bonus: Ingress
- [ ] Ingress controller running
- [ ] TLS certificate generated
- [ ] Secret created in cluster
- [ ] Both apps accessible via Ingress
- [ ] HTTPS working
- [ ] `/etc/hosts` configured

## Commands Reference

### Quick Deploy All Resources

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/deployment-nginx.yml
kubectl apply -f k8s/service-nginx.yml

# For bonus: setup Ingress
minikube addons enable ingress
cd k8s && ./generate-tls.sh
kubectl create secret tls devops-tls-secret --key tls.key --cert tls.crt -n devops
kubectl apply -f k8s/ingress.yml
```

### Monitoring and Debugging

```bash
# Watch all resources
kubectl get all -n devops

# Detailed pod info
kubectl describe pod <pod-name> -n devops

# View logs
kubectl logs -n devops -l app=devops-python --tail=100

# Follow logs in real-time
kubectl logs -n devops -l app=devops-python -f

# Get events
kubectl get events -n devops --sort-by='.lastTimestamp'

# Execute command in pod
kubectl exec -it <pod-name> -n devops -- sh
```

### Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Delete namespace (removes everything)
kubectl delete namespace devops

# Stop cluster
minikube stop

# Delete cluster
minikube delete
```

## Testing Scenarios

### 1. Test High Availability

```bash
# Delete one pod
kubectl delete pod <pod-name> -n devops

# Watch it automatically recreate
kubectl get pods -n devops -w

# Service remains available during recreation
curl http://localhost:8080/
```

### 2. Test Load Distribution

```bash
# Port-forward to service
kubectl port-forward -n devops service/devops-python-service 8080:80

# Make multiple requests, check different pod hostnames
for i in {1..20}; do 
  curl -s http://localhost:8080/ | jq -r '.system.hostname'
done
```

### 3. Test Rolling Update

```bash
# Trigger update
kubectl set image deployment/devops-python-app \
  devops-python=dmitry567/devops-info-service:latest \
  -n devops

# Watch rollout in real-time
kubectl rollout status deployment/devops-python-app -n devops
```

## Production Best Practices Implemented

### 1. Resource Management
- CPU and memory requests ensure proper scheduling
- Limits prevent resource exhaustion
- Pods are evenly distributed across nodes

### 2. Health Checks
- **Liveness probe**: Restarts unhealthy containers
- **Readiness probe**: Removes unready pods from service
- Prevents traffic to failing instances

### 3. Security
- Non-root user (UID 1000)
- Dropped all Linux capabilities
- Read-only root filesystem where possible

### 4. High Availability
- Multiple replicas (3+)
- Rolling update strategy
- MaxUnavailable: 1 (always 2+ pods available)
- MaxSurge: 1 (controlled resource usage)

### 5. Networking
- Service abstraction decouples apps from pods
- Ingress provides single entry point
- TLS encryption for secure communication

## Files Created

```
k8s/
├── namespace.yml              # Namespace isolation
├── configmap.yml              # Configuration management
├── deployment.yml             # Python app deployment (3 replicas)
├── service.yml                # Python app service
├── deployment-nginx.yml       # Nginx app deployment (2 replicas)
├── service-nginx.yml          # Nginx app service
├── ingress.yml                # Ingress with TLS and path routing
├── generate-tls.sh            # TLS certificate generation script
└── README.md                  # This documentation
```

## Screenshots Required

Save screenshots to `k8s/screenshots/`:

### Task 1:
- `cluster-info.png` - Output of `kubectl cluster-info`
- `nodes.png` - Output of `kubectl get nodes`

### Task 2:
- `deployments.png` - Output of `kubectl get deployments -n devops`
- `pods.png` - Output of `kubectl get pods -n devops -o wide`
- `deployment-describe.png` - Output of `kubectl describe deployment devops-python-app -n devops`

### Task 3:
- `services.png` - Output of `kubectl get services -n devops`
- `app-response.png` - Browser or curl showing app accessible

### Task 4:
- `scaling-5-replicas.png` - Output showing 5 pods running
- `rollout-status.png` - Rolling update in progress
- `rollout-history.png` - Output of `kubectl rollout history`

### Bonus:
- `ingress-status.png` - Output of `kubectl get ingress -n devops`
- `tls-certificate.png` - Certificate generation output
- `app1-https.png` - Browser showing https://devops.local/app1
- `app2-https.png` - Browser showing https://devops.local/app2
- `curl-ingress.png` - curl commands testing both paths

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n devops

# View pod events
kubectl describe pod <pod-name> -n devops

# Check logs
kubectl logs <pod-name> -n devops
```

**Common issues:**
- ImagePullBackOff: Docker image not found
- CrashLoopBackOff: Container exits immediately
- Pending: Insufficient resources

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n devops

# Verify service selector matches pod labels
kubectl get pods -n devops --show-labels
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress devops-apps-ingress -n devops

# View ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

## Key Learning Points

1. **Declarative Configuration**: YAML manifests define desired state
2. **Self-Healing**: Kubernetes automatically restarts failed containers
3. **Scaling**: Horizontal scaling is simple and instant
4. **Rolling Updates**: Zero-downtime deployments with automatic rollback
5. **Service Discovery**: Built-in DNS for service-to-service communication
6. **Resource Management**: Proper scheduling and isolation
7. **Ingress**: Advanced HTTP routing with TLS termination

## Next Steps

After completing this lab:
1. Take all required screenshots
2. Test all scenarios
3. Document any challenges encountered
4. Explore additional kubectl commands
5. Try kubectl dashboard: `minikube dashboard`

## Conclusion

This lab demonstrates production-ready Kubernetes deployment with:
- Multi-replica deployments for high availability
- Proper health checks and resource limits
- Service abstraction for stable networking
- Rolling updates with zero downtime
- Ingress with TLS for secure, routed access

All tasks and bonus requirements are implemented and ready for testing.
