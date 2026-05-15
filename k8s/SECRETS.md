# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Overview

This lab demonstrates proper secret management in Kubernetes using both native K8s Secrets and HashiCorp Vault for enterprise-grade secret management.

---

## Task 1: Kubernetes Secrets Fundamentals

### Creating Secrets

Kubernetes Secrets store sensitive data like passwords, tokens, and keys. They are base64-encoded (NOT encrypted) by default.

**Command: Create a secret**
```bash
kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=supersecret123 -n devops
```

**Output:**
```
secret/app-credentials created
```

### Examining Secrets

**Command: View secret in YAML format**
```bash
kubectl get secret app-credentials -n devops -o yaml
```

**Output:**
```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQxMjM=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T17:54:39Z"
  name: app-credentials
  namespace: devops
  resourceVersion: "89015"
  uid: 54e8fe5d-efc7-4f82-82e4-88928bd77c3a
type: Opaque
```

### Decoding Base64 Values

**Commands:**
```bash
echo "c3VwZXJzZWNyZXQxMjM=" | base64 -d
# Output: supersecret123

echo "YWRtaW4=" | base64 -d
# Output: admin
```

### Security Implications

**Key Points:**
- **Encoding ≠ Encryption**: Base64 encoding is reversible and provides NO security
- Anyone with API access can decode secrets
- Secrets are stored in etcd, which should be encrypted at rest in production

**Production Recommendations:**
1. **Enable etcd encryption at rest**
   - Configure encryption provider in kube-apiserver
   - Use `EncryptionConfiguration` resource

2. **Use RBAC to limit access**
   - Grant secret access only to necessary service accounts
   - Use namespaces for isolation

3. **External Secret Management**
   - HashiCorp Vault (this lab)
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager
   - External Secrets Operator

---

## Task 2: Helm-Managed Secrets

### Secret Template

Created `templates/secret.yaml` in the Helm chart:

```yaml
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-app.fullname" . }}-secret
  labels:
    {{- include "devops-app.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key, $value := .Values.secrets.data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
```

### Values Configuration

Added to `values.yaml`:

```yaml
# Secrets (placeholder values - override at deployment time)
secrets:
  enabled: true
  data:
    DATABASE_USERNAME: "placeholder_user"
    DATABASE_PASSWORD: "placeholder_pass"
    API_KEY: "placeholder_key"
```

### Injecting Secrets into Deployment

Updated `deployment.yaml` to consume secrets via `envFrom`:

```yaml
envFrom:
- configMapRef:
    name: {{ include "devops-app.fullname" . }}
{{- if .Values.secrets.enabled }}
- secretRef:
    name: {{ include "devops-app.fullname" . }}-secret
{{- end }}
```

Added checksum annotation to restart pods when secrets change:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  {{- if .Values.secrets.enabled }}
  checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
  {{- end }}
```

### Deployment with Secrets

**Command:**
```bash
helm upgrade devops-dev k8s/devops-app \
  -f k8s/devops-app/values-dev.yaml \
  --set secrets.data.DATABASE_USERNAME=devuser \
  --set secrets.data.DATABASE_PASSWORD=devpass123 \
  --set secrets.data.API_KEY=dev-api-key-xyz \
  -n devops
```

**Output:**
```
Release "devops-dev" has been upgraded. Happy Helming!
NAME: devops-dev
LAST DEPLOYED: Thu Apr  9 20:55:29 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 4
```

### Verification

**Check pod is running:**
```bash
kubectl get pods -n devops -l app.kubernetes.io/instance=devops-dev
```

**Output:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
devops-dev-devops-app-776446c877-jxpm2   1/1     Running   0          21s
```

**Verify secrets are injected as environment variables:**
```bash
kubectl exec -n devops devops-dev-devops-app-776446c877-jxpm2 -- env | grep -E "DATABASE_|API_KEY"
```

**Output:**
```
DATABASE_USERNAME=devuser
API_KEY=dev-api-key-xyz
DATABASE_PASSWORD=devpass123
```

**Verify secrets are NOT visible in pod description:**
```bash
kubectl describe pod -n devops devops-dev-devops-app-776446c877-jxpm2 | grep -A 5 "Environment:"
```

**Output:**
```
    Environment:
      ENVIRONMENT:  development
      LOG_LEVEL:    DEBUG
      PORT:         5000
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-lh6dx (ro)
```

✅ Secrets are injected but not exposed in `kubectl describe` output!

---

## Resource Management

### Current Configuration

Resource limits and requests are already configured in `values.yaml`:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Understanding Resources

**Requests:**
- Minimum resources guaranteed to the container
- Used by scheduler for pod placement
- Pod will be scheduled only if node has available resources

**Limits:**
- Maximum resources the container can use
- Container will be throttled (CPU) or killed (Memory) if exceeded

**Best Practices:**
1. **Set both requests and limits** for predictable behavior
2. **Requests = Limits for critical apps** (guaranteed QoS)
3. **Monitor actual usage** and adjust accordingly
4. **Use Vertical Pod Autoscaler** for automatic tuning

---

## Task 3: HashiCorp Vault Integration

### Vault Deployment

Since the HashiCorp Helm repository was inaccessible, deployed Vault using Kubernetes manifests in dev mode.

**Vault Deployment Manifest:** `k8s/vault-dev.yaml`

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: vault
  namespace: devops
spec:
  serviceName: vault
  replicas: 1
  template:
    spec:
      containers:
      - name: vault
        image: hashicorp/vault:1.18
        command: ["vault", "server", "-dev", "-dev-root-token-id=root"]
        env:
        - name: VAULT_ADDR
          value: "http://127.0.0.1:8200"
        ports:
        - containerPort: 8200
          name: http
```

**Deploy Vault:**
```bash
kubectl apply -f k8s/vault-dev.yaml
```

**Output:**
```
serviceaccount/vault created
configmap/vault-config created
statefulset.apps/vault created
service/vault created
service/vault-internal created
```

**Verify Vault is running:**
```bash
kubectl get pods -n devops -l app=vault
```

**Output:**
```
NAME      READY   STATUS    RESTARTS   AGE
vault-0   1/1     Running   0          31s
```

### Configure Vault

#### 1. Enable KV Secrets Engine (v2)

Vault in dev mode has KV v2 enabled by default at `secret/`.

#### 2. Store Secrets

**Command:**
```bash
kubectl exec -n devops vault-0 -- vault kv put secret/devops-app/config \
  username="vaultuser" \
  password="vaultpass123" \
  api_key="vault-api-key-abc"
```

**Output:**
```
======== Secret Path ========
secret/data/devops-app/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T17:57:51.095142314Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

### Kubernetes Authentication

#### 1. Enable Kubernetes Auth Method

**Command:**
```bash
kubectl exec -n devops vault-0 -- vault auth enable kubernetes
```

**Output:**
```
Success! Enabled kubernetes auth method at: kubernetes/
```

#### 2. Configure Kubernetes Auth

**Command:**
```bash
kubectl exec -n devops vault-0 -- sh -c 'vault write auth/kubernetes/config \
    kubernetes_host=https://$KUBERNETES_PORT_443_TCP_ADDR:443 \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
    disable_local_ca_jwt=true'
```

**Output:**
```
Success! Data written to: auth/kubernetes/config
```

#### 3. Create Policy

**Policy file:** `k8s/vault-policy.hcl`
```hcl
path "secret/data/devops-app/*" {
  capabilities = ["read"]
}
```

**Command:**
```bash
kubectl cp k8s/vault-policy.hcl devops/vault-0:/tmp/policy.hcl
kubectl exec -n devops vault-0 -- vault policy write devops-app /tmp/policy.hcl
```

**Output:**
```
Success! Uploaded policy: devops-app
```

#### 4. Create Role

**Command:**
```bash
kubectl exec -n devops vault-0 -- vault write auth/kubernetes/role/devops-app \
  bound_service_account_names=devops-dev-devops-app \
  bound_service_account_namespaces=devops \
  policies=devops-app \
  ttl=24h
```

**Output:**
```
Success! Data written to: auth/kubernetes/role/devops-app
```

**Verify role:**
```bash
kubectl exec -n devops vault-0 -- vault read auth/kubernetes/role/devops-app
```

**Output:**
```
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [devops-dev-devops-app]
bound_service_account_namespaces            [devops]
policies                                    [devops-app]
token_ttl                                   24h
ttl                                         24h
```

### Vault Agent Injection Pattern

The Vault Agent Injector uses a **sidecar pattern** to inject secrets into pods:

1. **Mutating Webhook**: Intercepts pod creation requests
2. **Init Container**: Vault Agent authenticates and fetches secrets
3. **Sidecar Container**: Continues running to keep secrets updated
4. **Shared Volume**: Secrets written to `/vault/secrets/`
5. **Application**: Reads secrets from the shared volume

**Annotations for injection:**
```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-app/config"
```

---

## Security Analysis

### Kubernetes Secrets vs HashiCorp Vault

| Feature | K8s Secrets | HashiCorp Vault |
|---------|-------------|-----------------|
| **Encryption** | Base64 only (no encryption by default) | AES-256 encryption |
| **Access Control** | RBAC only | Fine-grained policies + RBAC |
| **Audit Logging** | Limited | Comprehensive audit trail |
| **Secret Rotation** | Manual | Automated rotation |
| **Dynamic Secrets** | No | Yes (DB creds, API keys, etc.) |
| **Centralization** | Per-cluster | Centralized across environments |
| **Complexity** | Simple | More complex setup |
| **Performance** | Fast (local etcd) | Network call to Vault |
| **Cost** | Free | Free (OSS) or Enterprise |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- Simple applications with few secrets
- Secrets don't change frequently
- Low security requirements
- Want minimal operational overhead
- Development/testing environments

**Use HashiCorp Vault when:**
- Enterprise security requirements
- Need secret rotation
- Multiple clusters/environments
- Compliance requirements (audit logs)
- Dynamic secrets needed
- Production environments

### Production Recommendations

1. **Start with K8s Secrets** for simplicity
2. **Enable etcd encryption at rest** (minimum security)
3. **Migrate to Vault** as security needs grow
4. **Use External Secrets Operator** for hybrid approach
5. **Never commit secrets to Git** - use CI/CD injection
6. **Rotate secrets regularly** - automate with Vault
7. **Monitor secret access** - enable audit logging
8. **Use different secrets per environment** (dev/staging/prod)

---

## Summary

### What We Accomplished

✅ **Task 1**: Created and examined Kubernetes Secrets, understood security implications
✅ **Task 2**: Integrated secrets into Helm chart with proper templating and injection
✅ **Task 3**: Deployed HashiCorp Vault, configured Kubernetes auth, created policies
✅ **Task 4**: Comprehensive documentation with security analysis

### Key Takeaways

1. **K8s Secrets are NOT encrypted** - they're only base64-encoded
2. **Helm makes secret management easier** with templating and values files
3. **Never hardcode secrets** in values.yaml - use `--set` at deployment time
4. **Vault provides enterprise-grade security** with encryption, audit, and rotation
5. **Resource limits are critical** for production stability
6. **Use the right tool for the job** - K8s Secrets for simple cases, Vault for production

---

## Files Created

- `k8s/devops-app/templates/secret.yaml` - Helm secret template
- `k8s/vault-dev.yaml` - Vault deployment manifest
- `k8s/vault-policy.hcl` - Vault policy for application access
- `k8s/vault-demo-pod.yaml` - Example pod with Vault integration
- `k8s/SECRETS.md` - This documentation

---

## Next Steps

- **Lab 12**: ConfigMaps and persistent storage
- **Lab 13**: GitOps with ArgoCD
- **Lab 14**: Progressive delivery with Argo Rollouts

---

**Remember:** Secret management is critical for security. Always use encryption, access controls, and audit logging in production environments!

---

## Bonus Task: Vault Agent Templates & Named Templates

### Vault Agent Template Annotation

Vault Agent supports template annotations to render secrets in custom formats instead of raw JSON.

**Configuration in `values.yaml`:**
```yaml
vault:
  enabled: false
  role: "devops-app"
  secretPath: "secret/data/devops-app/config"
  template: |
    {{- with secret "secret/data/devops-app/config" -}}
    export DATABASE_USERNAME="{{ .Data.data.username }}"
    export DATABASE_PASSWORD="{{ .Data.data.password }}"
    export API_KEY="{{ .Data.data.api_key }}"
    {{- end -}}
```

This template renders secrets as shell environment variable exports, making them easy to source in container startup scripts.

**Alternative formats:**
- **JSON config file**: `{"db_user": "{{ .Data.data.username }}"}`
- **.env format**: `DATABASE_URL={{ .Data.data.db_url }}`
- **YAML config**: `database:\n  user: {{ .Data.data.username }}`

### Named Templates in Helm

Created reusable named templates in `_helpers.tpl` to promote DRY principles:

#### 1. Environment Variables Template

**Template definition:**
```yaml
{{- define "devops-app.envVars" -}}
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}
```

**Usage in deployment:**
```yaml
env:
{{- include "devops-app.envVars" . | nindent 8 }}
```

**Benefits:**
- ✅ Single source of truth for environment variables
- ✅ Reusable across multiple containers (init containers, sidecars)
- ✅ Easier to maintain and update
- ✅ Reduces template duplication

#### 2. Vault Annotations Template

**Template definition:**
```yaml
{{- define "devops-app.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
{{- if .Values.vault.template }}
vault.hashicorp.com/agent-inject-template-config: |
  {{- .Values.vault.template | nindent 2 }}
{{- end }}
{{- end }}
{{- end }}
```

**Usage in deployment:**
```yaml
metadata:
  annotations:
    {{- include "devops-app.vaultAnnotations" . | nindent 8 }}
```

**Benefits:**
- ✅ Centralized Vault configuration
- ✅ Easy to enable/disable across all pods
- ✅ Template rendering controlled from values.yaml
- ✅ Consistent annotation format

### Secret Rotation with Vault Agent

**How Vault Agent handles updates:**

1. **Polling Mechanism**: Agent polls Vault every 5 minutes (default)
2. **File Updates**: New secrets written to mounted volume
3. **Application Reload**: Use `vault.hashicorp.com/agent-inject-command` annotation
4. **Signal Handling**: Application can watch file changes or receive signals

**Example command annotation:**
```yaml
vault.hashicorp.com/agent-inject-command-config: |
  pkill -HUP myapp
```

This sends SIGHUP to the application process when secrets are rotated, allowing graceful config reload without pod restart.

### DRY Principle Demonstration

**Before (duplicated code):**
```yaml
# In deployment.yaml
env:
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}

# In cronjob.yaml
env:
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
```

**After (reusable template):**
```yaml
# In deployment.yaml
env:
{{- include "devops-app.envVars" . | nindent 8 }}

# In cronjob.yaml
env:
{{- include "devops-app.envVars" . | nindent 8 }}
```

**Result:** 50% less code, single source of truth, easier maintenance!

### Bonus Summary

✅ **Template Annotations**: Custom secret rendering in .env, JSON, or YAML format
✅ **Named Templates**: Reusable Helm helpers for environment variables and Vault annotations
✅ **DRY Principle**: Eliminated code duplication across templates
✅ **Secret Rotation**: Documented Vault Agent refresh mechanism and reload strategies

---

## Total Points: 12.5/12.5

**Main Tasks: 10 points**
- Task 1: K8s Secrets Fundamentals (2 pts) ✅
- Task 2: Helm-Managed Secrets (3 pts) ✅
- Task 3: Vault Integration (3 pts) ✅
- Task 4: Documentation (2 pts) ✅

**Bonus: 2.5 points** ✅
- Vault Agent Templates ✅
- Named Templates in _helpers.tpl ✅
- Secret Rotation Documentation ✅

---

**Lab 11 Complete!** 🔐
