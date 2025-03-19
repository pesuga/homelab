# Vector Database Setup

This document provides information about the vector database setup in the homelab environment.

## Qdrant Vector Database

Qdrant is a vector database optimized for fast similarity search and vector matching. It's used for storing and searching vector embeddings for machine learning applications.

### Features

- Fast vector similarity search
- Filtering support during search
- Horizontal scalability
- REST API and gRPC interfaces
- Supports multiple distance metrics (Cosine, Euclidean, Dot product)
- Payload storage alongside vectors

### Access

- **Web UI & API**: https://qdrant.app.pesulabs.net
- **gRPC**: qdrant.app.pesulabs.net:6334 (if exposed)

### Usage Examples

#### Python Client

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Connect to Qdrant
client = QdrantClient(url="https://qdrant.app.pesulabs.net")

# Create a collection
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
)

# Add vectors
client.upsert(
    collection_name="my_collection",
    points=[
        models.PointStruct(
            id=1, 
            vector=[0.1, 0.2, 0.3, ...],  # 768-dimensional vector
            payload={"metadata": "example 1"}
        ),
        # More points...
    ]
)

# Search for similar vectors
search_result = client.search(
    collection_name="my_collection",
    query_vector=[0.1, 0.2, 0.3, ...],  # Your query vector
    limit=5
)
```

### Maintenance

- Data is stored in a PersistentVolume
- Backups can be performed by backing up the `/qdrant/storage` directory
- Monitoring is available through the `/metrics` endpoint (Prometheus compatible)

### Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [GitHub Repository](https://github.com/qdrant/qdrant)
- [Python Client](https://github.com/qdrant/qdrant-client)
