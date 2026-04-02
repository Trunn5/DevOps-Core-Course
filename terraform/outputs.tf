output "vm_public_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address
}

output "vm_name" {
  description = "VM instance name"
  value       = yandex_compute_instance.devops_vm.name
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address}"
}

