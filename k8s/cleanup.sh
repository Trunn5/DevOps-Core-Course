#!/bin/bash
# Cleanup script for Lab 9 Kubernetes resources

set -e

echo "🧹 Cleaning up Lab 9 Kubernetes Resources..."
echo ""

# Delete all resources in devops namespace
echo "Deleting all resources in devops namespace..."
kubectl delete -f ingress.yml --ignore-not-found=true
kubectl delete -f service-nginx.yml --ignore-not-found=true
kubectl delete -f deployment-nginx.yml --ignore-not-found=true
kubectl delete -f service.yml --ignore-not-found=true
kubectl delete -f deployment.yml --ignore-not-found=true
kubectl delete -f configmap.yml --ignore-not-found=true

echo ""
echo "Deleting TLS secret..."
kubectl delete secret devops-tls-secret -n devops --ignore-not-found=true

echo ""
echo "Deleting namespace..."
kubectl delete namespace devops --ignore-not-found=true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To stop the cluster:"
echo "  minikube stop"
echo ""
echo "To delete the cluster:"
echo "  minikube delete"
echo ""
