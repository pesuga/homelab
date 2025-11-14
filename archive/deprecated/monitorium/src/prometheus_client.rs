use anyhow::{Context, Result};
use reqwest::Client;
use serde::Deserialize;
use std::collections::HashMap;
use tokio::time::{Duration, Instant};
use crate::mock_data::{NodeMetrics, ServiceMetrics};

#[derive(Debug, Clone, Deserialize)]
pub struct PrometheusConfig {
    pub url: String,
    pub timeout_secs: u64,
    pub query_interval_secs: u64,
}

impl Default for PrometheusConfig {
    fn default() -> Self {
        Self {
            url: "http://100.81.76.55:30090".to_string(),
            timeout_secs: 10,
            query_interval_secs: 5,
        }
    }
}

#[derive(Debug, Deserialize)]
struct PrometheusResponse {
    pub status: String,
    pub data: PrometheusData,
}

#[derive(Debug, Deserialize)]
struct PrometheusData {
    pub resultType: String,
    pub result: Vec<PrometheusMetric>,
}

#[derive(Debug, Deserialize)]
struct PrometheusMetric {
    pub metric: HashMap<String, String>,
    pub value: Vec<serde_json::Value>,
}

impl PrometheusMetric {
    pub fn value(&self) -> f64 {
        // Prometheus returns [timestamp, value], so we want the second element (index 1)
        if self.value.len() >= 2 {
            match &self.value[1] {
                serde_json::Value::Number(n) => n.as_f64().unwrap_or(0.0),
                serde_json::Value::String(s) => s.parse().unwrap_or(0.0),
                _ => 0.0,
            }
        } else {
            0.0
        }
    }
}

pub struct PrometheusClient {
    client: Client,
    config: PrometheusConfig,
    last_update: Option<Instant>,
    cached_nodes: HashMap<String, NodeMetrics>,
    cached_services: HashMap<String, ServiceMetrics>,
}

impl PrometheusClient {
    pub fn new(config: PrometheusConfig) -> Result<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            config,
            last_update: None,
            cached_nodes: HashMap::new(),
            cached_services: HashMap::new(),
        })
    }

    pub async fn update_metrics(&mut self) -> Result<bool> {
        let now = Instant::now();

        // Check if we need to update based on interval
        if let Some(last) = self.last_update {
            if now.duration_since(last) < Duration::from_secs(self.config.query_interval_secs) {
                return Ok(false); // No update needed
            }
        }

        // Update node metrics
        match self.fetch_node_metrics().await {
            Ok(nodes) => {
                self.cached_nodes = nodes;
            }
            Err(e) => {
                eprintln!("Warning: Failed to fetch node metrics: {}", e);
                // Don't return error immediately, try services too
            }
        }

        // Update service metrics
        match self.fetch_service_metrics().await {
            Ok(services) => {
                self.cached_services = services;
            }
            Err(e) => {
                eprintln!("Warning: Failed to fetch service metrics: {}", e);
            }
        }

        self.last_update = Some(now);
        Ok(true) // Updated successfully
    }

    pub fn get_nodes(&self) -> &HashMap<String, NodeMetrics> {
        &self.cached_nodes
    }

    pub fn get_services(&self) -> &HashMap<String, ServiceMetrics> {
        &self.cached_services
    }

    async fn fetch_node_metrics(&self) -> Result<HashMap<String, NodeMetrics>> {
        let mut nodes = HashMap::new();

        // Start with fallback mock data with real hardware specs
        nodes.insert("pesubuntu".to_string(), NodeMetrics {
            name: "pesubuntu".to_string(),
            ip_address: "192.168.8.106".to_string(),
            status: "Ready".to_string(),
            cpu_usage: 25.0,
            memory_usage: 45.0,
            memory_total: 0,
            gpu_usage: 0.0,
            gpu_memory: 0.0,
            gpu_memory_total: 0,
            network_rx: 0.0,
            network_tx: 0.0,
            disk_usage: 52.0,
            uptime: 0,
            temperature: 65.0,
            // Hardware specifications
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
            cpu_usage: 42.0,
            memory_usage: 68.0,
            memory_total: 0,
            gpu_usage: 0.0,
            gpu_memory: 0.0,
            gpu_memory_total: 0,
            network_rx: 0.0,
            network_tx: 0.0,
            disk_usage: 78.0,
            uptime: 0,
            temperature: 42.0,
            // Hardware specifications (service node specs)
            cpu_model: "Intel Core i7-4510U".to_string(),
            cpu_cores: 2,
            cpu_threads: 4,
            memory_total_gb: 8.0,
            gpu_model: "Integrated Intel HD Graphics".to_string(),
            disk_total_gb: 98.0,
        });

        // Try to get real metrics from Prometheus
        if let Ok(cpu_result) = self.query_prometheus("100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").await {
            self.update_node_cpu(&mut nodes, &cpu_result);
        }

        if let Ok(mem_result) = self.query_prometheus("((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)").await {
            self.update_node_memory(&mut nodes, &mem_result);
        }

        Ok(nodes)
    }

    async fn fetch_service_metrics(&self) -> Result<HashMap<String, ServiceMetrics>> {
        let mut services = HashMap::new();

        // Start with fallback mock data
        services.insert("n8n-0".to_string(), ServiceMetrics {
            name: "n8n-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 15.0,
            memory_usage: 35.0,
            requests_per_sec: 45.0,
            response_time: 125.0,
            error_rate: 0.2,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "http://n8n.homelab.svc.cluster.local:5678/healthz".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("postgres-0".to_string(), ServiceMetrics {
            name: "postgres-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 8.0,
            memory_usage: 25.0,
            requests_per_sec: 125.0,
            response_time: 45.0,
            error_rate: 0.0,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "postgres://postgres.homelab.svc.cluster.local:5432/homelab".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("redis-0".to_string(), ServiceMetrics {
            name: "redis-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 3.0,
            memory_usage: 18.0,
            requests_per_sec: 280.0,
            response_time: 12.0,
            error_rate: 0.0,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "redis://redis.homelab.svc.cluster.local:6379".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("prometheus-0".to_string(), ServiceMetrics {
            name: "prometheus-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 22.0,
            memory_usage: 42.0,
            requests_per_sec: 89.0,
            response_time: 89.0,
            error_rate: 0.0,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "http://prometheus.homelab.svc.cluster.local:9090/-/healthy".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("grafana-0".to_string(), ServiceMetrics {
            name: "grafana-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 12.0,
            memory_usage: 28.0,
            requests_per_sec: 23.0,
            response_time: 156.0,
            error_rate: 0.1,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "http://grafana.homelab.svc.cluster.local:3000/api/health".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("qdrant-0".to_string(), ServiceMetrics {
            name: "qdrant-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 18.0,
            memory_usage: 38.0,
            requests_per_sec: 67.0,
            response_time: 234.0,
            error_rate: 0.3,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "http://qdrant.homelab.svc.cluster.local:6333/health".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        services.insert("flowise-0".to_string(), ServiceMetrics {
            name: "flowise-0".to_string(),
            namespace: "homelab".to_string(),
            status: "Running".to_string(),
            cpu_usage: 25.0,
            memory_usage: 45.0,
            requests_per_sec: 34.0,
            response_time: 456.0,
            error_rate: 1.2,
            uptime: 0,
            replicas: 1,
            ready_replicas: 1,
            // Health probe info
            health_status: "Unknown".to_string(),
            health_endpoint: "http://flowise.homelab.svc.cluster.local:3000/api/v1/health".to_string(),
            last_health_check: 0,
            health_response_time: 0.0,
            consecutive_failures: 0,
        });

        // Try to get real service status from Prometheus
        if let Ok(up_result) = self.query_prometheus("up{job=\"postgres\"}").await {
            self.update_service_status(&mut services, &up_result, "postgres-0");
        }

        if let Ok(up_result) = self.query_prometheus("up{job=\"n8n\"}").await {
            self.update_service_status(&mut services, &up_result, "n8n-0");
        }

        if let Ok(up_result) = self.query_prometheus("up{job=\"redis\"}").await {
            self.update_service_status(&mut services, &up_result, "redis-0");
        }

        if let Ok(up_result) = self.query_prometheus("up{job=\"prometheus\"}").await {
            self.update_service_status(&mut services, &up_result, "prometheus-0");
        }

        Ok(services)
    }

    async fn query_prometheus(&self, query: &str) -> Result<PrometheusResponse> {
        let url = format!("{}/api/v1/query", self.config.url);
        let params = [("query", query)];

        let response = self.client
            .get(&url)
            .query(&params)
            .send()
            .await
            .context("Failed to send request to Prometheus")?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!("Prometheus returned status: {}", response.status()));
        }

        let prometheus_response: PrometheusResponse = response
            .json()
            .await
            .context("Failed to parse Prometheus response")?;

        Ok(prometheus_response)
    }

    fn update_node_cpu(&self, nodes: &mut HashMap<String, NodeMetrics>, result: &PrometheusResponse) {
        for metric in &result.data.result {
            if let Some(instance) = metric.metric.get("instance") {
                let node_name = if instance.contains("100.72.98.106") || instance.contains("pesubuntu") {
                    "pesubuntu"
                } else if instance.contains("asuna") {
                    "asuna"
                } else {
                    continue;
                };

                if let Some(node) = nodes.get_mut(node_name) {
                    node.cpu_usage = metric.value();
                }
            }
        }
    }

    fn update_node_memory(&self, nodes: &mut HashMap<String, NodeMetrics>, result: &PrometheusResponse) {
        for metric in &result.data.result {
            if let Some(instance) = metric.metric.get("instance") {
                let node_name = if instance.contains("100.72.98.106") || instance.contains("pesubuntu") {
                    "pesubuntu"
                } else if instance.contains("asuna") {
                    "asuna"
                } else {
                    continue;
                };

                if let Some(node) = nodes.get_mut(node_name) {
                    node.memory_usage = metric.value();
                }
            }
        }
    }

    fn update_service_cpu(&self, services: &mut HashMap<String, ServiceMetrics>, result: &PrometheusResponse) {
        for metric in &result.data.result {
            if let Some(name) = metric.metric.get("name") {
                let service_name = if name.contains("n8n") {
                    "n8n-0"
                } else if name.contains("postgres") {
                    "postgres-0"
                } else if name.contains("redis") {
                    "redis-0"
                } else if name.contains("prometheus") {
                    "prometheus-0"
                } else if name.contains("grafana") {
                    "grafana-0"
                } else if name.contains("qdrant") {
                    "qdrant-0"
                } else if name.contains("flowise") {
                    "flowise-0"
                } else {
                    continue;
                };

                if let Some(service) = services.get_mut(service_name) {
                    service.cpu_usage = metric.value();
                }
            }
        }
    }

    fn update_service_status(&self, services: &mut HashMap<String, ServiceMetrics>, result: &PrometheusResponse, service_name: &str) {
        if let Some(metric) = result.data.result.first() {
            let is_up = metric.value() == 1.0;
            if let Some(service) = services.get_mut(service_name) {
                service.status = if is_up { "Running".to_string() } else { "Stopped".to_string() };
            }
        }
    }

    pub async fn test_connection(&self) -> Result<bool> {
        // Test basic connectivity with a simple query
        let result = self.query_prometheus("up").await?;
        Ok(!result.data.result.is_empty())
    }
}