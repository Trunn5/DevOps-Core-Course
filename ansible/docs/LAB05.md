# Lab 05 — Ansible Fundamentals

## Architecture Overview

- **Ansible**: 13.4.0 (ansible-core 2.20)
- **Target VM**: Ubuntu 24.04 LTS (Yandex Cloud, 93.77.177.221)
- **Roles**: common, docker, app_deploy
- **Vault**: credentials encrypted with `ansible-vault`

### Structure

```
ansible/
├── inventory/hosts.ini
├── roles/
│   ├── common/        # System packages, timezone
│   ├── docker/        # Docker CE installation
│   └── app_deploy/    # Pull & run container
├── playbooks/
│   ├── provision.yml  # common + docker
│   ├── deploy.yml     # app_deploy
│   └── site.yml       # all roles
├── group_vars/all.yml # Vault-encrypted credentials
├── ansible.cfg
└── .vault_pass        # Gitignored
```

**Why roles?** Reusable, modular, testable independently. Each role has single responsibility.

---

## Roles

### common
- **Purpose**: Install essential packages, set timezone
- **Variables**: `common_packages` (list), `timezone`
- **Handlers**: none
- **Dependencies**: none

### docker
- **Purpose**: Install Docker CE from official repo
- **Variables**: `docker_user`, `docker_packages`
- **Handlers**: `restart docker`
- **Dependencies**: common (runs before docker)

### app_deploy
- **Purpose**: Pull Docker image, run container, health check
- **Variables**: `docker_image`, `docker_image_tag`, `app_port`, `app_container_name`, `app_restart_policy`
- **Handlers**: `restart app container`
- **Dependencies**: docker (must be installed first)

---

## Idempotency

### First run (changed=4)

```
TASK [docker : Install Docker packages]       changed
TASK [docker : Add user to docker group]       changed
TASK [docker : Install python3-docker]         changed
HANDLER [docker : restart docker]              changed
PLAY RECAP: ok=12 changed=4
```

### Second run (changed=0)

```
PLAY RECAP: ok=11 changed=0
```

All tasks green — desired state already achieved. Modules like `apt: state=present` and `service: state=started` only act when needed.

---

## Ansible Vault

```bash
ansible-vault create group_vars/all.yml   # Create encrypted file
ansible-vault edit group_vars/all.yml     # Edit
ansible-vault view group_vars/all.yml     # View
```

Encrypted file is safe to commit. Vault password stored in `.vault_pass` (gitignored).

Variables stored: `dockerhub_username`, `dockerhub_password`, `docker_image`, `app_port`, `app_container_name`.

---

## Deployment Verification

```
$ ansible-playbook playbooks/deploy.yml
TASK [app_deploy : Pull Docker image]             ok
TASK [app_deploy : Run application container]      changed
TASK [app_deploy : Wait for application to be ready] ok
TASK [app_deploy : Verify health endpoint]         ok
TASK [app_deploy : Show health check result]       ok
  health_check.json: {"status": "healthy", "timestamp": "2026-02-26T20:28:47", "uptime_seconds": 7}

$ docker ps
CONTAINER ID  IMAGE                                 STATUS         PORTS                   NAMES
52fa54537f86  dmitry567/devops-info-service:latest   Up 1 minute    0.0.0.0:5000->5000/tcp  devops-app

$ curl http://93.77.177.221:5000/health
{"status": "healthy", "timestamp": "...", "uptime_seconds": 38}
```

---

## Key Decisions

- **Roles vs playbooks**: Roles encapsulate logic, defaults, handlers in one place. Easy to reuse across projects.
- **Reusability**: Docker role can be used in any project needing Docker. Variables in `defaults/` allow customization.
- **Idempotency**: Using `state: present` (not shell commands). Modules check current state before acting.
- **Handlers**: Only restart Docker when packages change. Avoids unnecessary restarts.
- **Vault**: Secrets encrypted at rest. Can be committed to Git safely. Decrypted only at runtime.

---

## Bonus: Dynamic Inventory

### Plugin / Script

Custom Python script (`inventory/yandex_cloud.py`) that queries Yandex Cloud API via `yc` CLI.

- Groups VMs by label `project=devops-course` → `webservers` group
- Maps public IP → `ansible_host`
- Sets `ansible_user=ubuntu`
- Filters only RUNNING instances

### `ansible-inventory --graph`

```
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--devops-vm
```

### Playbook run with dynamic inventory

```bash
ansible-playbook -i inventory/yandex_cloud.py playbooks/deploy.yml
# PLAY RECAP: ok=9 changed=3 — app deployed, health check passed
```

### Benefits vs static inventory

- **No manual IP updates** — when VM IP changes, script queries fresh data
- **Auto-discovery** — new VMs with `project=devops-course` label appear automatically
- **Scalability** — works for 1 VM or 100 VMs without config changes

