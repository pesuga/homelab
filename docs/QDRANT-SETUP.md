# Qdrant Vector Database Setup Guide

**Version**: 1.0
**Date**: 2025-10-25
**Qdrant Version**: v1.12.5

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Verification](#verification)
- [Usage Examples](#usage-examples)
- [Integration with N8n](#integration-with-n8n)
- [Integration with Flowise](#integration-with-flowise)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)

---

## Overview

Qdrant is a vector database optimized for storing and searching high-dimensional vectors. It's perfect for:
- **Retrieval-Augmented Generation (RAG)**: Store document embeddings for context-aware LLM responses
- **Semantic Search**: Find similar documents, code, or data based on meaning
- **Recommendation Systems**: Build content recommendations based on similarity
- **Agent Memory**: Persistent memory for LLM agents across sessions

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  N8n Workflow / Flowise / Custom App                        │
│  (generates embeddings via Ollama)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ HTTP (6333) or gRPC (6334)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Qdrant Service (qdrant.homelab.svc.cluster.local)         │
│  ┌───────────────────────────────────────┐                 │
│  │  Collections                          │                 │
│  │  ├── documents (768-dim vectors)      │                 │
│  │  ├── code (384-dim vectors)           │                 │
│  │  └── agent_memory (1536-dim vectors)  │                 │
│  └───────────────────────────────────────┘                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Persistent Storage (20Gi)                                  │
│  /qdrant/storage                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- K3s cluster running on service node (asuna)
- kubectl configured to access the cluster
- At least 2GB free memory on service node
- 20GB free disk space

---

## Installation

### Step 1: Deploy Qdrant to Kubernetes

```bash
# Apply the Qdrant manifest
kubectl apply -f infrastructure/kubernetes/databases/qdrant/qdrant.yaml

# Expected output:
# persistentvolumeclaim/qdrant-pvc created
# service/qdrant created
# service/qdrant-nodeport created
# statefulset.apps/qdrant created
```

### Step 2: Verify Deployment

```bash
# Check pod status
kubectl get pods -n homelab -l app=qdrant

# Expected output:
# NAME        READY   STATUS    RESTARTS   AGE
# qdrant-0    1/1     Running   0          2m

# Check services
kubectl get svc -n homelab | grep qdrant

# Expected output:
# qdrant            ClusterIP   10.43.x.x    <none>        6333/TCP,6334/TCP   2m
# qdrant-nodeport   NodePort    10.43.x.x    <none>        6333:30633/TCP      2m
```

### Step 3: Check Logs

```bash
# View Qdrant startup logs
kubectl logs -n homelab qdrant-0

# Look for successful startup messages:
# - "Qdrant HTTP listening on 0.0.0.0:6333"
# - "Qdrant gRPC listening on 0.0.0.0:6334"
```

---

## Verification

### Health Check

```bash
# From local machine (via Tailscale)
curl http://100.81.76.55:30633/healthz

# Expected output:
# {"title":"healthz","version":"1.12.5"}

# From inside the cluster
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl http://qdrant.homelab.svc.cluster.local:6333/healthz
```

### Create Test Collection

```bash
# Port-forward for local access (in a separate terminal)
kubectl port-forward -n homelab svc/qdrant 6333:6333

# Create a test collection (384-dimensional vectors, Cosine similarity)
curl -X PUT http://localhost:6333/collections/test_collection \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

# Expected output:
# {"result":true,"status":"ok","time":0.001}

# List collections
curl http://localhost:6333/collections

# Expected output:
# {"result":{"collections":[{"name":"test_collection"}]},"status":"ok","time":0.0001}

# Get collection details
curl http://localhost:6333/collections/test_collection

# Delete test collection (cleanup)
curl -X DELETE http://localhost:6333/collections/test_collection
```

---

## Usage Examples

### Example 1: Insert Vectors with Metadata

```bash
# Insert a single vector with payload (metadata)
curl -X PUT http://localhost:6333/collections/test_collection/points \
  -H 'Content-Type: application/json' \
  -d '{
    "points": [
      {
        "id": 1,
        "vector": [0.1, 0.2, 0.3, ... ],  # 384 dimensions
        "payload": {
          "text": "This is a sample document",
          "source": "manual_test",
          "timestamp": "2025-10-25T10:00:00Z"
        }
      }
    ]
  }'
```

### Example 2: Search for Similar Vectors

```bash
# Search for top 5 similar vectors
curl -X POST http://localhost:6333/collections/test_collection/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, 0.3, ... ],  # Query vector (384 dimensions)
    "limit": 5,
    "with_payload": true
  }'

# Response includes similar vectors with scores and payloads
```

### Example 3: Filter Search by Metadata

```bash
# Search with metadata filter
curl -X POST http://localhost:6333/collections/test_collection/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, 0.3, ... ],
    "filter": {
      "must": [
        {
          "key": "source",
          "match": {
            "value": "manual_test"
          }
        }
      ]
    },
    "limit": 5
  }'
```

---

## Integration with N8n

### N8n HTTP Request Node Configuration

**Use Case**: Store document embeddings in Qdrant after generating them with Ollama.

**Workflow Steps**:
1. **Trigger**: Webhook or schedule
2. **Get Document**: Fetch document text (from file, API, etc.)
3. **Generate Embedding**: HTTP Request to Ollama
   - URL: `http://100.72.98.106:11434/api/embeddings`
   - Method: POST
   - Body: `{"model": "nomic-embed-text", "prompt": "{{ $json.text }}"}`
4. **Store in Qdrant**: HTTP Request to Qdrant
   - URL: `http://qdrant.homelab.svc.cluster.local:6333/collections/documents/points`
   - Method: PUT
   - Body:
   ```json
   {
     "points": [{
       "id": "{{ $json.doc_id }}",
       "vector": "{{ $json.embedding }}",
       "payload": {
         "text": "{{ $json.text }}",
         "source": "{{ $json.source }}"
       }
     }]
   }
   ```

**N8n Node Settings**:
- Node: HTTP Request
- URL: `http://qdrant.homelab.svc.cluster.local:6333` (internal cluster access)
- Authentication: None (internal network)
- Headers: `Content-Type: application/json`

---

## Integration with Flowise

### Flowise Vector Store Configuration

Flowise has built-in Qdrant support.

**Setup Steps**:
1. Open Flowise at http://100.81.76.55:30850
2. Create a new flow
3. Add a **Qdrant** vector store node
4. Configure:
   - **Qdrant URL**: `http://qdrant.homelab.svc.cluster.local:6333`
   - **Collection Name**: `your_collection_name`
   - **API Key**: (leave empty for internal access)
5. Connect to **Document Loader** and **Embeddings** nodes
6. Test the flow

**Example Flow**:
```
Document Loader → Text Splitter → Embeddings (Ollama) → Qdrant → Conversational Retrieval QA
```

---

## Backup and Restore

### Create Snapshot

```bash
# Create a snapshot via API
curl -X POST http://localhost:6333/collections/documents/snapshots

# Response includes snapshot name:
# {"result":{"name":"documents-2025-10-25-10-00-00.snapshot"},"status":"ok"}

# Download snapshot
curl http://localhost:6333/collections/documents/snapshots/documents-2025-10-25-10-00-00.snapshot \
  -o backup.snapshot
```

### Restore from Snapshot

```bash
# Upload snapshot to Qdrant pod
kubectl cp backup.snapshot homelab/qdrant-0:/qdrant/snapshots/

# Restore collection
curl -X PUT http://localhost:6333/collections/documents/snapshots/upload \
  -F 'snapshot=@backup.snapshot'
```

### Automated Backup (Future Enhancement)

Create a CronJob to periodically snapshot collections:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: qdrant-backup
  namespace: homelab
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: curlimages/curl
            command:
            - sh
            - -c
            - |
              curl -X POST http://qdrant:6333/collections/documents/snapshots
              # Add upload to S3/backup volume
          restartPolicy: OnFailure
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n homelab qdrant-0

# Common issues:
# - Insufficient memory: Increase node resources or reduce limits
# - PVC pending: Check StorageClass availability
# - Image pull errors: Check network connectivity
```

### Connection Refused

```bash
# Verify service endpoints
kubectl get endpoints -n homelab qdrant

# Check if pod is ready
kubectl get pods -n homelab -l app=qdrant

# Test from inside cluster
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl http://qdrant:6333/healthz
```

### Collection Not Found

```bash
# List all collections
curl http://localhost:6333/collections

# Create missing collection
curl -X PUT http://localhost:6333/collections/my_collection \
  -H 'Content-Type: application/json' \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'
```

### Out of Memory

```bash
# Check Qdrant memory usage
kubectl top pod -n homelab qdrant-0

# If near limit (2Gi), consider:
# 1. Reducing collection size (delete old vectors)
# 2. Increasing memory limits in StatefulSet
# 3. Optimizing vector dimensions (use smaller models)
```

### Data Loss After Pod Restart

```bash
# Verify PVC is bound
kubectl get pvc -n homelab qdrant-pvc

# Check volume mount
kubectl exec -n homelab qdrant-0 -- ls -la /qdrant/storage

# If empty, PVC may not be properly mounted (check StatefulSet volumeMounts)
```

---

## Performance Tuning

### Vector Dimension Recommendations

| Model | Dimensions | Use Case | Memory Impact |
|-------|-----------|----------|---------------|
| `nomic-embed-text` | 768 | General text | Medium |
| `all-MiniLM-L6-v2` | 384 | Fast retrieval | Low |
| `text-embedding-ada-002` | 1536 | High accuracy | High |

**Rule of Thumb**: 1 million 768-dim vectors ≈ 3GB RAM

### Indexing Parameters

For large collections (>100k vectors), consider HNSW indexing:

```json
{
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100,
    "full_scan_threshold": 10000
  }
}
```

---

## API Reference

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check |
| `/collections` | GET | List all collections |
| `/collections/{name}` | PUT | Create collection |
| `/collections/{name}` | DELETE | Delete collection |
| `/collections/{name}/points` | PUT | Upsert points (vectors) |
| `/collections/{name}/points/search` | POST | Search similar vectors |
| `/collections/{name}/snapshots` | POST | Create snapshot |
| `/metrics` | GET | Prometheus metrics |

**Full API Docs**: https://qdrant.tech/documentation/interfaces/

---

## Next Steps

1. Create production collections for your use cases
2. Integrate with N8n workflows for RAG
3. Set up automated backups
4. Monitor via Grafana (Qdrant exports Prometheus metrics)
5. Optimize indexing for your data size

---

## Resources

- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **Python Client**: `pip install qdrant-client`
- **LangChain Integration**: https://python.langchain.com/docs/integrations/vectorstores/qdrant
- **Flowise Integration**: Built-in vector store node

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
