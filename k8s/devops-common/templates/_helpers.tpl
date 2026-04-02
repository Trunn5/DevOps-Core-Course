{{/*
Common labels that can be reused across charts
*/}}
{{- define "devops-common.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-common.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate standard resource limits
*/}}
{{- define "devops-common.resources" -}}
resources:
  limits:
    cpu: {{ .limits.cpu | default "500m" }}
    memory: {{ .limits.memory | default "256Mi" }}
  requests:
    cpu: {{ .requests.cpu | default "100m" }}
    memory: {{ .requests.memory | default "128Mi" }}
{{- end }}

{{/*
Generate standard health probes
*/}}
{{- define "devops-common.healthProbes" -}}
livenessProbe:
  httpGet:
    path: {{ .path | default "/health" }}
    port: {{ .port | default "http" }}
  initialDelaySeconds: {{ .livenessInitialDelay | default 10 }}
  periodSeconds: {{ .livenessPeriod | default 10 }}
  timeoutSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: {{ .path | default "/health" }}
    port: {{ .port | default "http" }}
  initialDelaySeconds: {{ .readinessInitialDelay | default 5 }}
  periodSeconds: {{ .readinessPeriod | default 5 }}
  timeoutSeconds: 3
  failureThreshold: 3
{{- end }}

{{/*
Generate standard security context
*/}}
{{- define "devops-common.securityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: {{ .runAsUser | default 1000 }}
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
{{- end }}

{{/*
Generate standard pod security context
*/}}
{{- define "devops-common.podSecurityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: {{ .runAsUser | default 1000 }}
  fsGroup: {{ .fsGroup | default 1000 }}
{{- end }}
