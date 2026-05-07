# Lab 6: Advanced Ansible & CI/CD

## Task 1: Blocks & Tags

### Common Role

Roles refactored with `block / rescue / always`:

- **packages** block — apt update + install; rescue runs `apt-get update --fix-missing`; always writes timestamp to `/tmp/ansible_common_done`.
- **users** block — timezone setup.
- Role-level tag `common` applied in `provision.yml`.

### Docker Role

- **docker_install** block — GPG key, repo, packages; rescue waits 10s and retries; always ensures Docker service is enabled.
- **docker_config** block — user group membership.
- Role-level tag `docker` applied in `provision.yml`.

### Tag Strategy

| Tag | Scope |
|-----|-------|
| `common` | entire common role |
| `packages` | apt packages only |
| `users` | user/timezone config |
| `docker` | entire docker role |
| `docker_install` | Docker packages only |
| `docker_config` | Docker user config |
| `app_deploy` | application deployment |
| `compose` | Docker Compose tasks |
| `web_app_wipe` | wipe tasks |

### Selective Execution

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --list-tags
```

### Research

- **Rescue also fails?** Ansible reports fatal error; `always` still executes.
- **Nested blocks?** Yes, blocks can contain blocks.
- **Tag inheritance?** Tasks inside a block inherit tags applied to the block.

---

## Task 2: Docker Compose

### Migration from `docker run`

Renamed `app_deploy` → `web_app`. Added Jinja2 template `docker-compose.yml.j2`:

```yaml
version: '3.8'
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      PORT: "{{ app_internal_port }}"
    restart: unless-stopped
```

### Role Dependencies

`roles/web_app/meta/main.yml` declares `docker` as a dependency — running only the `web_app` role auto-installs Docker first.

### Deployment Flow

1. Create `/opt/{{ app_name }}` directory
2. Template `docker-compose.yml`
3. `docker compose pull` + `docker compose up -d`
4. Wait for port + health check

### Research

- **`always` vs `unless-stopped`?** `always` restarts even after manual stop; `unless-stopped` does not.
- **Compose vs bridge networks?** Compose creates an isolated network per project; bridge is Docker's shared default.
- **Vault vars in templates?** Yes, Ansible decrypts them before Jinja2 rendering.

---

## Task 3: Wipe Logic

Double-gated by **variable** (`web_app_wipe: false` by default) and **tag** (`web_app_wipe`).

### Scenarios

| # | Command | Result |
|---|---------|--------|
| 1 | `ansible-playbook deploy.yml` | normal deploy, wipe skipped |
| 2 | `deploy.yml -e "web_app_wipe=true" --tags web_app_wipe` | wipe only |
| 3 | `deploy.yml -e "web_app_wipe=true"` | wipe → fresh deploy |
| 4 | `deploy.yml --tags web_app_wipe` | variable false → wipe skipped |

### Wipe Actions

1. `docker compose down --remove-orphans`
2. Remove compose file
3. Remove app directory

### Research

- **Why both variable AND tag?** Prevents accidental wipe — need explicit opt-in on both levels.
- **Difference from `never` tag?** `never` requires `--tags never` to run; this approach uses a custom tag + variable for finer control and documentation.
- **Why wipe before deploy?** Enables clean reinstall in a single playbook run.
- **Clean reinstall vs rolling update?** Clean removes all state; rolling keeps the service available during update.
- **Extending wipe?** Add `docker image prune -f` and `docker volume prune -f` tasks.

---

## Task 4: CI/CD

### Workflow: `.github/workflows/ansible-deploy.yml`

**Jobs:**

1. **lint** — installs `ansible-lint`, runs on all playbooks
2. **deploy** — sets up SSH, creates inventory from secrets, runs `ansible-playbook deploy.yml`, verifies with curl

**Path filters:** triggers on `ansible/**` changes (excluding `docs/`).

**GitHub Secrets required:**

| Secret | Purpose |
|--------|---------|
| `SSH_PRIVATE_KEY` | SSH key to VM |
| `VM_HOST` | Target VM IP |
| `VM_USER` | SSH username |
| `ANSIBLE_VAULT_PASSWORD` | Vault decryption |

**Badge:**

```
![Ansible Deployment](https://github.com/trunn5/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)
```

### Research

- **SSH keys in Secrets?** Encrypted at rest, exposed only to workflow runs. Rotate regularly; use deploy keys with minimal scope.
- **Staging → production?** Add separate inventory files and jobs with manual approval gate for production.
- **Rollbacks?** Pin `docker_tag` to specific version; revert the variable and re-run the playbook.
- **Self-hosted vs GitHub-hosted?** Self-hosted avoids exposing SSH keys externally; runner stays inside the network.

---

## Bonus 1: Multi-App Deployment

### Architecture

Same `web_app` role deployed twice with different variables:

| App | Image | Host Port | Internal Port |
|-----|-------|-----------|---------------|
| devops-python | dmitry567/devops-info-service | 5000 | 5000 |
| devops-scala | dmitry567/devops-info-service-scala | 5001 | 5000 |

Variable files: `vars/app_python.yml`, `vars/app_scala.yml`.

Playbooks: `deploy_python.yml`, `deploy_scala.yml`, `deploy_all.yml`.

Wipe is app-specific — each playbook sets its own `app_name` / `compose_project_dir`.

---

## Bonus 2: Multi-App CI/CD

Separate workflows for each app can be created with path filters on `vars/app_python.yml` vs `vars/app_scala.yml`. Changes to `roles/web_app/**` trigger both workflows.

---

## Summary

- Roles refactored with blocks, rescue/always, and a comprehensive tag strategy
- Migrated from `docker run` to Docker Compose with Jinja2 templates
- Wipe logic with double-gate safety (variable + tag)
- CI/CD workflow with linting, deployment, and verification
- Multi-app support via role reusability with different variable files
