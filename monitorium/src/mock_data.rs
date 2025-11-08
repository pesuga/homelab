use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct NodeMetrics {
    pub name: String,
    pub ip_address: String,
    pub status: String,
    pub cpu_usage: f64,
    pub memory_usage: f64,
    pub memory_total: u64,
    pub gpu_usage: f64,
    pub gpu_memory: f64,
    pub gpu_memory_total: u64,
    pub network_rx: f64,
    pub network_tx: f64,
    pub disk_usage: f64,
    pub uptime: u64,
    pub temperature: f64,
    // Hardware specification fields
    pub cpu_model: String,
    pub cpu_cores: u32,
    pub cpu_threads: u32,
    pub memory_total_gb: f64,
    pub gpu_model: String,
    pub disk_total_gb: f64,
}

#[derive(Debug, Clone)]
pub struct ServiceMetrics {
    pub name: String,
    pub namespace: String,
    pub status: String,
    pub cpu_usage: f64,
    pub memory_usage: f64,
    pub requests_per_sec: f64,
    pub response_time: f64,
    pub error_rate: f64,
    pub uptime: u64,
    pub replicas: u32,
    pub ready_replicas: u32,
    // Health probe fields
    pub health_status: String, // "Healthy", "Unhealthy", "Degraded", "Unknown"
    pub health_endpoint: String,
    pub last_health_check: u64, // Unix timestamp
    pub health_response_time: f64, // Health check response time in ms
    pub consecutive_failures: u32,
}

pub fn generate_mock_metrics() -> (HashMap<String, NodeMetrics>, HashMap<String, ServiceMetrics>) {
    let mut nodes = HashMap::new();
    let mut services = HashMap::new();

    // Nodes - matching your homelab setup
    nodes.insert("pesubuntu".to_string(), NodeMetrics {
        name: "pesubuntu".to_string(),
        ip_address: "192.168.8.106".to_string(),
        status: "Ready".to_string(),
        cpu_usage: 25.3,
        memory_usage: 45.2,
        memory_total: 32 * 1024 * 1024 * 1024, // 32GB in bytes
        gpu_usage: 67.8,
        gpu_memory: 55.4,
        gpu_memory_total: 16 * 1024 * 1024 * 1024, // 16GB in bytes
        network_rx: 450.2,
        network_tx: 320.8,
        disk_usage: 52.3,
        uptime: 86400 * 7, // 7 days
        temperature: 65.2,
        // Hardware specs
        cpu_model: "Intel Core i5-12400F".to_string(),
        cpu_cores: 6,
        cpu_threads: 12,
        memory_total_gb: 32.0,
        gpu_model: "AMD Radeon RX 7800 XT".to_string(),
        disk_total_gb: 937.0,
    });

    nodes.insert("asuna".to_string(), NodeMetrics {
        name: "asuna".to_string(),
        ip_address: "192.168.8.185".to_string(),
        status: "Ready".to_string(),
        cpu_usage: 42.7,
        memory_usage: 68.9,
        memory_total: 8 * 1024 * 1024 * 1024, // 8GB in bytes
        gpu_usage: 0.0, // No GPU on service node
        gpu_memory: 0.0,
        gpu_memory_total: 0,
        network_rx: 125.4,
        network_tx: 98.7,
        disk_usage: 78.5,
        uptime: 86400 * 30, // 30 days
        temperature: 42.1,
        // Hardware specs
        cpu_model: "Intel Core i7-4510U".to_string(),
        cpu_cores: 2,
        cpu_threads: 4,
        memory_total_gb: 8.0,
        gpu_model: "Integrated Intel HD Graphics".to_string(),
        disk_total_gb: 98.0,
    });

    // Services - matching your K3s setup
    services.insert("n8n-0".to_string(), ServiceMetrics {
        name: "n8n-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 15.2,
        memory_usage: 35.8,
        requests_per_sec: 45.3,
        response_time: 125.4,
        error_rate: 0.2,
        uptime: 86400 * 14, // 14 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for n8n
        health_status: "Healthy".to_string(),
        health_endpoint: "http://n8n.homelab.svc.cluster.local:5678/healthz".to_string(),
        last_health_check: 1733318400, // Recent timestamp
        health_response_time: 45.2,
        consecutive_failures: 0,
    });

    services.insert("postgres-0".to_string(), ServiceMetrics {
        name: "postgres-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 8.7,
        memory_usage: 25.4,
        requests_per_sec: 125.8,
        response_time: 45.2,
        error_rate: 0.0,
        uptime: 86400 * 30, // 30 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for PostgreSQL
        health_status: "Healthy".to_string(),
        health_endpoint: "postgres://postgres.homelab.svc.cluster.local:5432/homelab".to_string(),
        last_health_check: 1733318420, // Recent timestamp
        health_response_time: 12.8,
        consecutive_failures: 0,
    });

    services.insert("redis-0".to_string(), ServiceMetrics {
        name: "redis-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 3.2,
        memory_usage: 18.9,
        requests_per_sec: 280.5,
        response_time: 12.3,
        error_rate: 0.0,
        uptime: 86400 * 21, // 21 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for Redis
        health_status: "Healthy".to_string(),
        health_endpoint: "redis://redis.homelab.svc.cluster.local:6379".to_string(),
        last_health_check: 1733318435, // Recent timestamp
        health_response_time: 8.4,
        consecutive_failures: 0,
    });

    services.insert("prometheus-0".to_string(), ServiceMetrics {
        name: "prometheus-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 22.4,
        memory_usage: 42.1,
        requests_per_sec: 89.3,
        response_time: 89.7,
        error_rate: 0.0,
        uptime: 86400 * 25, // 25 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for Prometheus
        health_status: "Healthy".to_string(),
        health_endpoint: "http://prometheus.homelab.svc.cluster.local:9090/-/healthy".to_string(),
        last_health_check: 1733318450,
        health_response_time: 15.3,
        consecutive_failures: 0,
    });

    services.insert("grafana-0".to_string(), ServiceMetrics {
        name: "grafana-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 12.8,
        memory_usage: 28.3,
        requests_per_sec: 23.4,
        response_time: 156.8,
        error_rate: 0.1,
        uptime: 86400 * 18, // 18 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for Grafana
        health_status: "Healthy".to_string(),
        health_endpoint: "http://grafana.homelab.svc.cluster.local:3000/api/health".to_string(),
        last_health_check: 1733318465,
        health_response_time: 22.1,
        consecutive_failures: 0,
    });

    services.insert("qdrant-0".to_string(), ServiceMetrics {
        name: "qdrant-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 18.5,
        memory_usage: 38.7,
        requests_per_sec: 67.2,
        response_time: 234.5,
        error_rate: 0.3,
        uptime: 86400 * 12, // 12 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for Qdrant
        health_status: "Degraded".to_string(), // Show one with issues
        health_endpoint: "http://qdrant.homelab.svc.cluster.local:6333/health".to_string(),
        last_health_check: 1733318480,
        health_response_time: 125.6,
        consecutive_failures: 2,
    });

    services.insert("flowise-0".to_string(), ServiceMetrics {
        name: "flowise-0".to_string(),
        namespace: "homelab".to_string(),
        status: "Running".to_string(),
        cpu_usage: 25.9,
        memory_usage: 45.2,
        requests_per_sec: 34.6,
        response_time: 456.7,
        error_rate: 1.2,
        uptime: 86400 * 10, // 10 days
        replicas: 1,
        ready_replicas: 1,
        // Health probe info for Flowise
        health_status: "Unhealthy".to_string(), // Show one that's unhealthy
        health_endpoint: "http://flowise.homelab.svc.cluster.local:3000/api/v1/health".to_string(),
        last_health_check: 1733318490,
        health_response_time: 0.0, // No response
        consecutive_failures: 5,
    });

    (nodes, services)
}