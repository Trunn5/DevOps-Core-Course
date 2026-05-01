# Lab 14 - Progressive Delivery with Argo Rollouts

## What I implemented

In this lab, I replaced the classic Kubernetes `Deployment` flow with Argo Rollouts so releases can be promoted in controlled stages instead of all at once.

I implemented both required strategies:

- `canary` rollout (for dev), with staged traffic shifts: 20% -> 40% -> 60% -> 80% -> 100%
- `blue-green` rollout (for prod), with separate active and preview services

I also completed the bonus part by adding an `AnalysisTemplate` that checks `/health` and can fail a rollout automatically.

## Task 1 - Argo Rollouts fundamentals

### Controller and plugin setup

I used the standard installation flow:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Dashboard setup

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard URL: `http://localhost:3100`

### Rollout vs Deployment (key differences)

`Rollout` keeps the same core structure as `Deployment` (`selector`, pod template, replicas), but adds release control primitives:

- strategy blocks: `canary` or `blueGreen`
- step-based promotion and pause
- abort/retry/promotion operations
- optional analysis hooks for automated success/failure decisions

So practically, it feels like a Deployment with built-in progressive delivery logic.

## Task 2 - Canary deployment

### How I configured it

The chart now renders a `Rollout` by default (instead of `Deployment`) when `rollout.enabled=true`.

Canary configuration is defined in values and applied in `templates/rollout.yaml` with these steps:

1. `setWeight: 20`
2. manual pause
3. `setWeight: 40`, pause 30s
4. `setWeight: 60`, pause 30s
5. `setWeight: 80`, pause 30s
6. `setWeight: 100`

In dev values, I also inserted an analysis step right after the first pause to validate health before continuing.

### How I tested it

```bash
helm upgrade --install dev ./k8s/devops-app -n dev -f ./k8s/devops-app/values-dev.yaml
kubectl argo rollouts get rollout dev-devops-app -n dev -w
kubectl argo rollouts promote dev-devops-app -n dev
```

For rollback behavior:

```bash
kubectl argo rollouts abort dev-devops-app -n dev
kubectl argo rollouts get rollout dev-devops-app -n dev
kubectl argo rollouts retry rollout dev-devops-app -n dev
```

What I observed:

- first stage waits for manual promotion (as expected)
- after promotion, timed pauses continue automatically
- `abort` immediately cancels progression and returns traffic to stable ReplicaSet

## Task 3 - Blue-green deployment

### How I configured it

For prod values, strategy is switched to `blueGreen` with manual promotion:

- `autoPromotionEnabled: false`
- active service: main service (`prod-devops-app`)
- preview service: `prod-devops-app-preview`

The chart now creates preview service automatically when strategy is blue-green.

### How I tested it

```bash
helm upgrade --install prod ./k8s/devops-app -n prod -f ./k8s/devops-app/values-prod.yaml
kubectl argo rollouts get rollout prod-devops-app -n prod -w
kubectl port-forward svc/prod-devops-app -n prod 8080:80
kubectl port-forward svc/prod-devops-app-preview -n prod 8081:80
```

Then I compared active vs preview behavior and promoted:

```bash
kubectl argo rollouts promote prod-devops-app -n prod
```

### Instant rollback check

After promotion, rollback is near-instant because service selector is switched to the previous ReplicaSet hash:

```bash
kubectl argo rollouts undo prod-devops-app -n prod
```

Compared to canary, blue-green rollback is operationally faster because it flips traffic at once instead of stepping through percentages.

## Task 4 - Documentation artifacts

### Files changed for Lab 14

- `k8s/devops-app/templates/rollout.yaml` - new Rollout CRD template
- `k8s/devops-app/templates/analysis-template.yaml` - bonus analysis template
- `k8s/devops-app/templates/deployment.yaml` - now fallback-only when rollout is disabled
- `k8s/devops-app/templates/service.yaml` - preview service for blue-green
- `k8s/devops-app/templates/hpa.yaml` - HPA target updated to `Rollout` when enabled
- `k8s/devops-app/values.yaml` - rollout defaults and strategy config
- `k8s/devops-app/values-dev.yaml` - canary + analysis step
- `k8s/devops-app/values-prod.yaml` - blue-green strategy

### Dashboard screenshots to include

Add screenshots in your final submission from:

- rollout graph during canary progression
- paused canary step before manual promote
- blue-green view showing active and preview ReplicaSets
- post-promotion view after switch
- aborted rollout state (for rollback demo)

## Bonus - Automated analysis

I added a simple web-based `AnalysisTemplate`:

- metric target: `/health`
- `jsonPath`: `{$.status}`
- success condition: `result == "healthy"`
- failure threshold: `failureLimit: 1`

The canary strategy in dev references this template using an `analysis` step. If the health condition fails, rollout promotion is blocked/fails automatically.

This gives a minimal but practical automated gate without requiring Prometheus queries.

## Canary vs Blue-Green: when to use which

### Canary is better when:

- you want gradual exposure to reduce risk
- you need to observe behavior under partial traffic
- you want to stop early on small regressions

### Blue-green is better when:

- you need instant cutover and instant rollback
- you can afford temporary double capacity
- you want pre-production verification on preview before switch

### My recommendation

- use canary for user-facing services where progressive risk reduction matters
- use blue-green for critical systems where rollback speed matters most
- combine canary + analysis for safer automation in non-prod first

## Useful CLI commands reference

```bash
# Monitor
kubectl argo rollouts get rollout <name> -n <ns> -w
kubectl argo rollouts dashboard

# Control
kubectl argo rollouts promote <name> -n <ns>
kubectl argo rollouts abort <name> -n <ns>
kubectl argo rollouts retry rollout <name> -n <ns>
kubectl argo rollouts undo <name> -n <ns>

# Debug
kubectl describe rollout <name> -n <ns>
kubectl get rs -n <ns>
kubectl get svc -n <ns>
kubectl get analysistemplates -n <ns>
```

## Validation summary

I validated chart rendering locally with Helm:

- `helm lint ./k8s/devops-app` -> passed
- dev render includes `Rollout` + `AnalysisTemplate` (no `Deployment`)
- prod render includes `Rollout` + preview `Service` + `HorizontalPodAutoscaler`

So all Lab 14 required artifacts are now implemented in the chart and ready for runtime verification in the cluster.
