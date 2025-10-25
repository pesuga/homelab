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
