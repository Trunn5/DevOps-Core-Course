# Lab 04 — Infrastructure as Code

## Cloud Provider

- **Provider**: Yandex Cloud
- **Region**: ru-central1-a
- **Instance**: standard-v2, 2 vCPU (20%), 2 GB RAM, 10 GB HDD
- **OS**: Ubuntu 24.04 LTS
- **Cost**: Free tier

---

## Terraform

### Structure

```
terraform/
├── main.tf         # Provider, network, security group, VM
├── variables.tf    # Input variables
├── outputs.tf      # Public IP, SSH command
├── key.json        # Service account key (gitignored)
├── terraform.tfvars # Variable values (gitignored)
└── .gitignore      # State, credentials excluded
```

### Resources Created

| Resource | Description |
|----------|-------------|
| `yandex_vpc_network` | Virtual network |
| `yandex_vpc_subnet` | Subnet 10.0.1.0/24 |
| `yandex_vpc_security_group` | Ports: 22, 80, 5000 |
| `yandex_compute_instance` | Ubuntu 24.04 VM |

### Commands

```bash
cd terraform
terraform init      # Installed yandex-cloud/yandex v0.187.0
terraform plan      # Plan: 4 to add
terraform apply     # Apply complete! Resources: 4 added
# Output: ssh ubuntu@93.77.191.135
terraform destroy   # Destroy complete! Resources: 4 destroyed
```

### SSH Access (Terraform VM)

```
$ ssh ubuntu@93.77.191.135 "hostname; uname -a"
fhmvhf3cbv2brajc7ekg
Linux fhmvhf3cbv2brajc7ekg 6.8.0-100-generic ... x86_64 GNU/Linux
```

---

## Pulumi

### Structure

```
pulumi/
├── __main__.py       # All resources in Python
├── Pulumi.yaml       # Project config
├── requirements.txt  # pulumi + pulumi-yandex
└── .gitignore
```

### Same resources, different syntax — Python instead of HCL.

### Commands

```bash
cd pulumi
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export PULUMI_BACKEND_URL="file://."
export PULUMI_CONFIG_PASSPHRASE=""
pulumi stack init dev
pulumi config set ssh_public_key "$(cat ~/.ssh/id_ed25519.pub)"
pulumi config set yandex:cloud_id <CLOUD_ID>
pulumi config set yandex:folder_id <FOLDER_ID>
pulumi config set yandex:zone ru-central1-a
pulumi config set yandex:service_account_key_file /path/to/key.json
pulumi preview      # Resources: + 5 to create
pulumi up --yes     # Resources: + 5 created, Duration: 57s
# Output: ssh ubuntu@46.21.246.9
```

### SSH Access (Pulumi VM)

```
$ ssh ubuntu@46.21.246.9 "hostname; uname -a"
fhm69v5kuvur1rsvdbr8
Linux fhm69v5kuvur1rsvdbr8 6.8.0-100-generic ... x86_64 GNU/Linux
```

---

## Terraform vs Pulumi

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Язык** | HCL (декларативный) | Python (императивный) |
| **Читаемость** | Проще для инфры | Привычнее для разработчиков |
| **Логика** | Ограничена (count, for_each) | Полный язык (циклы, функции) |
| **State** | Локальный файл | Pulumi Cloud / локальный |
| **IDE** | Базовая поддержка | Автодополнение, типы |
| **Отладка** | terraform plan | print() + pulumi preview |

**Terraform лучше:** простая инфра, большая команда, много документации.
**Pulumi лучше:** сложная логика, разработчики в команде, тесты инфры.

---

## Bonus: IaC CI/CD + GitHub Import

### Part 1: Terraform CI Workflow

File: `.github/workflows/terraform-ci.yml`

Triggers on `terraform/**` changes (push + PR):
1. `terraform fmt -check` — formatting
2. `terraform init -backend=false` — init without state
3. `terraform validate` — syntax check
4. `tflint` — linting for best practices

### Part 2: GitHub Repository Import

Added `github.tf` — manages `Trunn5/DevOps-Core-Course` repo via Terraform.

```
$ terraform import github_repository.course_repo DevOps-Core-Course
github_repository.course_repo: Import prepared!
github_repository.course_repo: Refreshing state...
Import successful!

$ terraform plan
Plan: 4 to add, 0 to change, 0 to destroy.
# GitHub repo: no changes (state matches reality)
# 4 to add = Yandex Cloud resources (destroyed earlier, Pulumi VM is active)
```

**Why importing matters:**
- Version control for infrastructure changes
- Code review before any modification
- Audit trail (who changed what)
- Disaster recovery — recreate from code
- No manual "tribal knowledge" needed

---

## Lab 5 Preparation

- Pulumi VM оставлена запущенной для Lab 5 (Ansible)
- Подключение: `ssh ubuntu@46.21.246.9`
- Terraform ресурсы уничтожены (`terraform destroy`)
