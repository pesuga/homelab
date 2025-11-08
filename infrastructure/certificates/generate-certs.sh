#!/bin/bash
# Generate self-signed CA and wildcard certificate for homelab
# Usage: ./generate-certs.sh

set -e

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CA_DIR="${CERT_DIR}/ca"
DOMAIN="homelab.local"

echo "🔒 Generating self-signed certificates for *.${DOMAIN}"
echo ""

# Create directories
mkdir -p "${CA_DIR}"
cd "${CA_DIR}"

# 1. Generate Root CA
echo "📝 Step 1: Creating Root CA..."
if [ ! -f "ca-key.pem" ]; then
    openssl genrsa -out ca-key.pem 4096
    openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem \
        -subj "/C=US/ST=Home/L=Lab/O=Homelab/CN=Homelab Root CA"
    echo "✅ Root CA created"
else
    echo "ℹ️  Root CA already exists"
fi

# 2. Generate wildcard certificate
echo ""
echo "📝 Step 2: Creating wildcard certificate for *.${DOMAIN}..."

# Generate private key
openssl genrsa -out homelab-key.pem 4096

# Create config file for SAN
cat > openssl.cnf << EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
C = US
ST = Home
L = Lab
O = Homelab
CN = *.${DOMAIN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.${DOMAIN}
DNS.2 = ${DOMAIN}
DNS.3 = *.asuna.${DOMAIN}
DNS.4 = *.pesubuntu.${DOMAIN}
EOF

# Generate CSR
openssl req -new -key homelab-key.pem -out homelab.csr -config openssl.cnf

# Sign certificate with CA
openssl x509 -req -days 825 -in homelab.csr \
    -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
    -out homelab-cert.pem \
    -extensions req_ext -extfile openssl.cnf

echo "✅ Wildcard certificate created"

# 3. Verify certificate
echo ""
echo "📝 Step 3: Verifying certificate..."
openssl x509 -in homelab-cert.pem -text -noout | grep -A1 "Subject Alternative Name"

# 4. Display certificate info
echo ""
echo "📋 Certificate Information:"
echo "   Issuer: $(openssl x509 -in homelab-cert.pem -noout -issuer)"
echo "   Subject: $(openssl x509 -in homelab-cert.pem -noout -subject)"
echo "   Valid from: $(openssl x509 -in homelab-cert.pem -noout -startdate)"
echo "   Valid until: $(openssl x509 -in homelab-cert.pem -noout -enddate)"

# 5. Create README
cat > README.md << 'EOFREADME'
# Homelab SSL Certificates

This directory contains the self-signed CA and certificates for the homelab.

## Files

- `ca-cert.pem` - Root CA certificate (install on devices)
- `ca-key.pem` - Root CA private key (⚠️ KEEP SECURE)
- `homelab-cert.pem` - Wildcard certificate for *.homelab.local
- `homelab-key.pem` - Private key for wildcard certificate (⚠️ KEEP SECURE)

## Installation

### Install Root CA on devices to trust certificates

**Linux (Ubuntu/Debian)**:
```bash
sudo cp ca-cert.pem /usr/local/share/ca-certificates/homelab-ca.crt
sudo update-ca-certificates
```

**macOS**:
```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain ca-cert.pem
```

**Windows** (PowerShell as Admin):
```powershell
certutil -addstore -f "ROOT" ca-cert.pem
```

**Firefox** (all platforms):
1. Settings → Privacy & Security → Certificates → View Certificates
2. Authorities tab → Import
3. Select `ca-cert.pem`
4. Check "Trust this CA to identify websites"

## Usage

The wildcard certificate (`homelab-cert.pem`) is used by Traefik for all `*.homelab.local` domains.

## Security Notes

- **Private keys** (`ca-key.pem`, `homelab-key.pem`) must be kept secure
- Never commit private keys to git (already in .gitignore)
- Root CA is valid for 10 years
- Wildcard cert is valid for 825 days (~2.25 years)
- Regenerate certificates before expiry
EOFREADME

echo ""
echo "✅ Certificate generation complete!"
echo ""
echo "📁 Files created in: ${CA_DIR}"
echo "   - ca-cert.pem (Root CA - install on devices)"
echo "   - ca-key.pem (Root CA private key - KEEP SECURE)"
echo "   - homelab-cert.pem (Wildcard certificate)"
echo "   - homelab-key.pem (Private key - KEEP SECURE)"
echo ""
echo "📖 Next steps:"
echo "   1. Install Root CA on your devices (see README.md)"
echo "   2. Create Kubernetes secret with certificate"
echo "   3. Deploy Traefik ingress controller"
echo ""
