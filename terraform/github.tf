# GitHub provider is configured in main.tf required_providers block

provider "github" {
  token = var.github_token
  owner = "Trunn5"
}

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "\U0001f680Production-grade DevOps course: 18 hands-on labs covering Docker, Kubernetes, Helm, Terraform, Ansible, CI/CD, GitOps (ArgoCD), monitoring (Prometheus/Grafana), and more. Build real-world skills with progressive delivery, secrets management, and cloud-native deployments."
  visibility  = "public"

  has_issues    = false
  has_wiki      = true
  has_projects  = true
  has_downloads = true

  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = true
  delete_branch_on_merge = false
  archived               = false
}
