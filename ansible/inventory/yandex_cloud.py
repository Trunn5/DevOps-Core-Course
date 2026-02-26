#!/usr/bin/env python3
"""
Dynamic inventory script for Yandex Cloud.
Queries running VMs via `yc` CLI and groups them by labels.
"""

import json
import subprocess
import sys


def get_instances():
    """Get running instances from Yandex Cloud."""
    try:
        result = subprocess.run(
            ["yc", "compute", "instance", "list", "--format", "json"],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return []


def build_inventory(instances):
    """Build Ansible inventory from instances list."""
    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"hosts": [], "children": ["webservers"]},
        "webservers": {"hosts": []},
    }

    for inst in instances:
        if inst.get("status") != "RUNNING":
            continue

        name = inst["name"]
        # Get public IP
        public_ip = None
        for iface in inst.get("network_interfaces", []):
            one_to_one = iface.get("primary_v4_address", {}).get("one_to_one_nat", {})
            public_ip = one_to_one.get("address")
            if public_ip:
                break

        if not public_ip:
            continue

        inventory["all"]["hosts"].append(name)

        # Group by label 'project=devops-course'
        labels = inst.get("labels", {})
        if labels.get("project") == "devops-course":
            inventory["webservers"]["hosts"].append(name)

        inventory["_meta"]["hostvars"][name] = {
            "ansible_host": public_ip,
            "ansible_user": "ubuntu",
            "ansible_ssh_private_key_file": "~/.ssh/id_ed25519",
        }

    return inventory


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        instances = get_instances()
        inventory = build_inventory(instances)
        print(json.dumps(inventory, indent=2))
    elif len(sys.argv) == 2 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        print(json.dumps({"_meta": {"hostvars": {}}}))


if __name__ == "__main__":
    main()

