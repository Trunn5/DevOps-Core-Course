#!/bin/bash
# Quick deployment script for Lab 9 Kubernetes resources

set -e

echo "🚀 Deploying Lab 9 Kubernetes Resources..."
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install it first:"
    echo "   brew install kubectl"
    exit 1
fi

# Check if cluster is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not running. Please start it first:"
    echo "   minikube start"
    echo "   OR"
    echo "   kind create cluster --name devops-lab9"
    exit 1
fi

echo "✅ Cluster is running"
echo ""

# Deploy resources
echo "📦 Creating namespace..."
kubectl apply -f namespace.yml

echo "📦 Creating ConfigMap..."
kubectl apply -f configmap.yml

echo "📦 Deploying Python application..."
kubectl apply -f deployment.yml

echo "📦 Creating Python service..."
kubectl apply -f service.yml

echo "📦 Deploying Nginx application..."
kubectl apply -f deployment-nginx.yml

echo "📦 Creating Nginx service..."
kubectl apply -f service-nginx.yml

echo ""
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=120s \
  deployment/devops-python-app -n devops

kubectl wait --for=condition=available --timeout=120s \
  deployment/devops-nginx-app -n devops

echo ""
echo "✅ All deployments ready!"
echo ""

# Show status
echo "📊 Current Status:"
echo ""
kubectl get all -n devops

echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Test Python app:"
echo "   kubectl port-forward -n devops service/devops-python-service 8080:80"
echo "   curl http://localhost:8080/"
echo ""
echo "2. For Ingress (bonus):"
echo "   minikube addons enable ingress"
echo "   ./generate-tls.sh"
echo "   kubectl create secret tls devops-tls-secret --key tls.key --cert tls.crt -n devops"
echo "   kubectl apply -f ingress.yml"
echo ""
echo "3. View in browser:"
echo "   minikube service devops-python-service -n devops"
echo ""
