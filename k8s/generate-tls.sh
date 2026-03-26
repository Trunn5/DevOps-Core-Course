#!/bin/bash
# Generate self-signed TLS certificate for Kubernetes Ingress

set -e

echo "Generating self-signed TLS certificate for devops.local..."

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=devops.local/O=DevOps-Lab9"

echo "Certificate generated successfully!"
echo ""
echo "Files created:"
echo "  - tls.key (private key)"
echo "  - tls.crt (certificate)"
echo ""
echo "Next steps:"
echo "1. Create Kubernetes secret:"
echo "   kubectl create secret tls devops-tls-secret --key tls.key --cert tls.crt -n devops"
echo ""
echo "2. View certificate details:"
echo "   openssl x509 -in tls.crt -text -noout"
echo ""
echo "3. Add to /etc/hosts:"
echo "   sudo sh -c \"echo '\$(minikube ip) devops.local' >> /etc/hosts\""
