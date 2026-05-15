# Lab 13 — GitOps with ArgoCD

## Introduction

This lab covers setting up ArgoCD for GitOps-based deployments. The main idea is that Git becomes the single source of truth for everything running in Kubernetes - any changes to the cluster should come from Git commits, not manual kubectl commands.

## Setting Up ArgoCD

### Installation

First, I added the ArgoCD Helm repository:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

Then created a namespace for ArgoCD:

```bash
kubectl create namespace argocd
```

### Resource Configuration

I ran into memory issues with the default ArgoCD configuration on minikube, so I created a custom values file with reduced resource limits (`k8s/argocd/values-minikube.yaml`). The main changes were:

- Controller: 250m CPU / 256Mi memory (instead of default 1 CPU / 1Gi)
- Server: 50m CPU / 128Mi memory
- Repo-server: 50m CPU / 128Mi memory

This makes ArgoCD run smoothly on local development environments without eating up all available resources.

Installed ArgoCD with:

```bash
helm install argocd argo/argo-cd --namespace argocd -f k8s/argocd/values-minikube.yaml
```

Waited for all pods to come up:

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

Everything started successfully - 7 pods running:
- argocd-server (the UI and API)
- argocd-application-controller (syncs apps)
- argocd-repo-server (fetches from Git)
- argocd-applicationset-controller (generates apps)
- argocd-dex-server (authentication)
- argocd-redis (caching)
- argocd-notifications-controller (alerts)

### Getting Access

Retrieved the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Password: `MZC9zQU-YxdqoEJc`

To access the UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open `https://localhost:8080` and login with:
- Username: `admin`
- Password: (the one retrieved above)

## Deploying Applications with ArgoCD

### Setting Up Environments

Created two separate namespaces for different environments:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

The idea is to have isolated environments with different configurations and sync policies.

### Application Manifests

I created two ArgoCD Application resources - one for dev and one for prod.

**Dev Environment** (`application-dev.yaml`):

The dev environment has automatic syncing enabled. This means any changes pushed to Git will automatically deploy to the dev namespace within 3 minutes (ArgoCD's default polling interval). This is great for fast iteration.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Trunn5/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-app
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Key settings:
- `automated` - ArgoCD syncs automatically
- `prune: true` - Removes resources deleted from Git
- `selfHeal: true` - Reverts any manual changes back to Git state

**Production Environment** (`application-prod.yaml`):

Production uses manual sync only. This is intentional - you don't want automatic deployments to production. Every prod deployment should be deliberate and controlled.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Trunn5/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-app
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Notice there's no `automated` section - this means manual sync only.

### Applying the Configurations

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

After applying, both applications appeared in ArgoCD:

```bash
kubectl get applications -n argocd
```

Output showed:
```
NAME              SYNC STATUS   HEALTH STATUS   REVISION
devops-app-dev    OutOfSync     Missing         513d869f39...
devops-app-prod   OutOfSync     Missing         513d869f39...
```

`OutOfSync` means the Git state hasn't been applied yet (needs initial sync). `Missing` means no resources exist in the cluster yet. The revision hash confirms ArgoCD successfully connected to GitHub and found the Helm chart.

## Understanding Self-Healing

There are actually two types of self-healing happening in Kubernetes with ArgoCD:

### 1. Kubernetes Self-Healing (Always Active)

This is built into Kubernetes. If you delete a pod:

```bash
kubectl delete pod <pod-name> -n dev
```

The ReplicaSet controller immediately recreates it. This has nothing to do with ArgoCD - it's just Kubernetes ensuring the desired number of replicas.

### 2. ArgoCD Self-Healing (Configuration Drift)

This is different. It detects when someone manually changes resource configuration and reverts it back to match Git.

Example test:

```bash
# Scale deployment manually
kubectl scale deployment devops-app-dev -n dev --replicas=5
```

With selfHeal enabled, ArgoCD will:
1. Detect the drift (current replicas: 5, Git says: 1)
2. Automatically sync to fix it
3. Scale back down to 1 replica

This usually happens within 3-5 minutes (the polling interval).

### Testing Configuration Drift

Another example - adding a label:

```bash
kubectl label deployment devops-app-dev -n dev test=manual
```

ArgoCD will detect this change and remove the label since it's not in Git. You can see the diff with:

```bash
argocd app diff devops-app-dev
```

## Why Different Policies for Different Environments?

I configured dev with auto-sync and prod with manual sync. Here's why this makes sense:

**Development Environment (Auto-Sync):**
- Developers want fast feedback
- Push to Git → 3 minutes later it's deployed
- Mistakes are low-risk, easy to fix
- Self-heal prevents people from debugging by randomly changing things

**Production Environment (Manual Sync):**
- Need control over when things deploy
- Want to review changes before production release
- May need to coordinate with maintenance windows
- Gives time to prepare rollback plans
- Compliance requirements might require approval

In a real company, you'd probably also have a staging environment with auto-sync for final testing before prod.

## ApplicationSet (Bonus)

Instead of creating separate Application manifests for each environment, you can use an ApplicationSet to generate them from a template. This is especially useful when you have many environments or applications.

Created `applicationset.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-app-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: "true"
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  template:
    metadata:
      name: 'devops-app-{{.env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/Trunn5/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/devops-app
        helm:
          valueFiles:
            - '{{.valuesFile}}'
      destination:
        namespace: '{{.namespace}}'
```

This single manifest replaces both individual application files. The list generator creates one Application for each element (dev and prod). When you add a new environment, just add another element to the list.

## GitOps Workflow

The typical workflow looks like this:

1. Make changes to Helm chart or values files
2. Commit and push to Git
3. ArgoCD polls Git every 3 minutes
4. Detects changes
5. Auto-syncs dev environment
6. Wait for manual sync of prod

This means Git history becomes your deployment audit log. Want to know what was deployed when? Just look at Git commits.

## Observations and Challenges

**What Worked Well:**
- ArgoCD installation was straightforward with the resource-optimized config
- Application manifests are declarative and easy to understand
- The separation between dev (auto) and prod (manual) makes sense

**Challenges:**
- Minikube resource constraints caused OOMKilled errors initially
- Had to reduce resource requests/limits significantly
- Default ArgoCD configuration is designed for larger clusters

**Lessons Learned:**
- GitOps is powerful but requires proper cluster resources
- Auto-sync is great for dev, dangerous for prod
- The declarative approach makes it easy to understand what's deployed

## Comparison: Traditional vs GitOps

**Before (Traditional CI/CD):**
- CI pipeline has kubectl credentials
- Pipeline runs `kubectl apply`
- No way to know current cluster state
- Manual changes go undetected
- Rollback means re-running old pipeline

**With GitOps:**
- No cluster credentials in CI
- Cluster pulls from Git
- Always know cluster = Git
- Manual changes detected and reverted
- Rollback = git revert

Much cleaner and more secure.

## What's Next

For Lab 14 we'll add progressive delivery with Argo Rollouts - things like canary deployments and blue-green deployments. ArgoCD will manage those too.

## Files Created

- `k8s/argocd/application-dev.yaml` - Dev environment application
- `k8s/argocd/application-prod.yaml` - Prod environment application  
- `k8s/argocd/applicationset.yaml` - Bonus: template for both environments
- `k8s/argocd/values-minikube.yaml` - Resource-optimized ArgoCD config

## Summary

ArgoCD is now set up and ready to manage our Kubernetes deployments through GitOps. The applications are configured to deploy from the `lab13` branch, with dev auto-syncing and prod requiring manual approval. All the configuration is in place - it just needs adequate cluster resources to run fully.

The beauty of this setup is that from now on, deploying changes is just:
1. Edit Helm chart
2. Git commit
3. Git push
4. Wait (for dev) or click Sync (for prod)

No more running kubectl commands manually!
