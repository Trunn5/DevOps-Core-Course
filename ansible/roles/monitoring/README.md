# Monitoring Role

Ansible role for deploying Grafana Loki logging stack with Promtail and Grafana.

## Features

- ✅ Loki 3.0 with TSDB storage
- ✅ Promtail with Docker service discovery
- ✅ Grafana 11.3 with auto-configured Loki data source
- ✅ Multi-app support (Python, Scala)
- ✅ Resource limits and health checks
- ✅ 7-day log retention by default
- ✅ Fully idempotent
- ✅ All configs templated with Jinja2

## Requirements

- Ansible 2.16+
- `community.docker` collection
- Docker role (dependency)

## Role Variables

See `defaults/main.yml` for all 55+ variables.

**Key variables:**

```yaml
# Service versions
loki_version: "3.0.0"
promtail_version: "3.0.0"
grafana_version: "11.3.0"

# Ports
loki_port: 3100
grafana_port: 3000
promtail_port: 9080

# Retention
loki_retention_period: 168h  # 7 days

# Grafana
grafana_admin_password: "admin"
grafana_anonymous_enabled: false

# Apps to monitor
monitored_apps:
  - name: devops-python
    image: dmitry567/devops-info-service
    port: 8000
    ...
```

## Dependencies

Defined in `meta/main.yml`:
- `docker` role (ensures Docker is installed)

## Example Playbook

```yaml
---
- name: Deploy Monitoring Stack
  hosts: webservers
  become: true

  roles:
    - monitoring
```

With custom variables:

```yaml
- name: Deploy Monitoring with custom retention
  hosts: webservers
  become: true

  roles:
    - role: monitoring
      vars:
        loki_retention_period: 336h  # 14 days
        grafana_admin_password: "{{ vault_grafana_password }}"
```

## Usage

```bash
# Deploy
ansible-playbook playbooks/deploy-monitoring.yml

# Deploy with custom password
ansible-playbook playbooks/deploy-monitoring.yml \
  -e "grafana_admin_password=secure123"

# Test idempotency
ansible-playbook playbooks/deploy-monitoring.yml
ansible-playbook playbooks/deploy-monitoring.yml  # Should show "ok", not "changed"

# Only run setup (skip deployment)
ansible-playbook playbooks/deploy-monitoring.yml --tags monitoring_setup

# Only run deployment (skip setup)
ansible-playbook playbooks/deploy-monitoring.yml --tags monitoring_deploy
```

## What It Does

1. **Creates directory structure:**
   - `/opt/monitoring/`
   - `/opt/monitoring/loki/`
   - `/opt/monitoring/promtail/`

2. **Templates configurations:**
   - `loki/config.yml` — TSDB schema, retention, limits
   - `promtail/config.yml` — Docker SD, relabeling
   - `docker-compose.yml` — All services with resource limits

3. **Deploys with Docker Compose:**
   - Uses `docker_compose_v2` module
   - Pulls latest images
   - Starts all services

4. **Waits for health:**
   - Loki: `/ready` endpoint
   - Grafana: `/api/health` endpoint

5. **Auto-configures Grafana:**
   - Creates Loki data source via API
   - Sets as default data source
   - No manual UI steps needed

## Handlers

- `restart monitoring` — Restarts stack when configs change

## Tags

- `monitoring` — Entire role
- `monitoring_setup` — Setup phase only
- `monitoring_deploy` — Deploy phase only

## Outputs

After successful deployment:
- Grafana: `http://<host>:3000`
- Loki: `http://<host>:3100`
- Username: `admin`
- Password: `<grafana_admin_password>`

## Idempotency

✅ Second run shows no changes if:
- Configs haven't changed
- Containers already running
- Grafana data source already exists

## Testing

```bash
# Verify services
ssh user@vm
cd /opt/monitoring
docker compose ps  # All should be healthy

# Test Loki
curl http://localhost:3100/ready

# Test Grafana
curl http://localhost:3000/api/health

# Check logs
docker compose logs loki
docker compose logs promtail
docker compose logs grafana
```

## License

MIT

## Author

DevOps Core Course - Lab 7
