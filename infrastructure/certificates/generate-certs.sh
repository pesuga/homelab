#!/bin/bash
# Script to generate self-signed wildcard certificate for *.homelab.local

# Create directory for certificates
mkdir -p /tmp/homelab-certs
cd /tmp/homelab-certs

# Generate the CA private key
openssl genrsa -out homelab-ca.key 4096

# Generate the CA certificate
openssl req -x509 -new -nodes -key homelab-ca.key -sha256 -days 3650 \
  -out homelab-ca.crt -subj "/CN=Homelab CA/O=Homelab/C=US"

# Generate the server private key
openssl genrsa -out homelab-tls.key 2048

# Create CSR config file
cat > homelab-csr.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
CN = *.homelab.local
O = Homelab
C = US

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.homelab.local
DNS.2 = homelab.local
EOF

# Generate the CSR
openssl req -new -key homelab-tls.key -out homelab-tls.csr \
  -config homelab-csr.conf

# Generate the certificate
openssl x509 -req -in homelab-tls.csr -CA homelab-ca.crt \
  -CAkey homelab-ca.key -CAcreateserial -out homelab-tls.crt \
  -days 3650 -sha256 -extensions req_ext -extfile homelab-csr.conf

# Create Kubernetes TLS secret
kubectl create namespace cert-storage || true
kubectl create secret tls homelab-tls -n cert-storage \
  --cert=homelab-tls.crt --key=homelab-tls.key

# Output results
echo "Certificate generated successfully!"
echo "Secret 'homelab-tls' created in namespace 'cert-storage'"
echo ""
echo "CA certificate: /tmp/homelab-certs/homelab-ca.crt - import this into your browser/system"
echo "Server certificate: /tmp/homelab-certs/homelab-tls.crt"
echo "Server key: /tmp/homelab-certs/homelab-tls.key"
