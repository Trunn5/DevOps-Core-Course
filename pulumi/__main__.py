"""DevOps Info Service — Yandex Cloud VM with Pulumi."""
import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
zone = config.get("zone") or "ru-central1-a"
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_public_key = config.require("ssh_public_key")

# Network
network = yandex.VpcNetwork("devops-network")

subnet = yandex.VpcSubnet("devops-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"])

# Security group
security_group = yandex.VpcSecurityGroup("devops-sg",
    network_id=network.id,
    ingresses=[
        {"description": "SSH", "protocol": "TCP", "port": 22, "v4_cidr_blocks": ["0.0.0.0/0"]},
        {"description": "HTTP", "protocol": "TCP", "port": 80, "v4_cidr_blocks": ["0.0.0.0/0"]},
        {"description": "App", "protocol": "TCP", "port": 5000, "v4_cidr_blocks": ["0.0.0.0/0"]},
    ],
    egresses=[
        {"description": "Allow all outbound", "protocol": "ANY", "v4_cidr_blocks": ["0.0.0.0/0"]},
    ])

# Get latest Ubuntu image
image = yandex.get_compute_image(family="ubuntu-2404-lts")

# VM instance
instance = yandex.ComputeInstance("devops-vm",
    zone=zone,
    platform_id="standard-v2",
    resources={"cores": 2, "memory": 2, "core_fraction": 20},
    boot_disk={"initialize_params": {"image_id": image.id, "size": 10, "type": "network-hdd"}},
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [security_group.id],
    }],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
    },
    labels={"project": "devops-course", "lab": "lab04"})

# Outputs
pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", instance.name)
pulumi.export("ssh_command", instance.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {ssh_user}@{ip}"))

