use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use dirs::home_dir;

/// Main configuration structure for Monitorium
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// General application settings
    pub general: GeneralConfig,

    /// Prometheus configuration for metrics collection
    pub prometheus: PrometheusConfig,

    /// Service health check configurations
    pub health_checks: HealthCheckConfig,

    /// Node monitoring configuration
    pub nodes: NodeConfig,

    /// UI and display configuration
    pub ui: UiConfig,

    /// Logging configuration
    pub logging: LoggingConfig,
}

/// General application settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneralConfig {
    /// Update interval in seconds for metrics collection
    pub update_interval_secs: u64,

    /// History retention period in data points
    pub history_retention: usize,

    /// Connection timeout in seconds
    pub connection_timeout_secs: u64,

    /// Whether to start in fullscreen mode
    pub fullscreen: bool,

    /// Theme to use (default, dark, light)
    pub theme: String,
}

/// Prometheus configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrometheusConfig {
    /// Prometheus server URL
    pub url: String,

    /// Connection timeout in seconds
    pub timeout_secs: u64,

    /// Query interval in seconds
    pub query_interval_secs: u64,

    /// Custom Prometheus queries for nodes
    pub node_queries: NodeQueries,

    /// Custom Prometheus queries for services
    pub service_queries: ServiceQueries,

    /// Authentication (optional)
    pub auth: Option<PrometheusAuth>,
}

/// Custom Prometheus queries for node metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeQueries {
    /// CPU usage query
    pub cpu_usage: String,

    /// Memory usage query
    pub memory_usage: String,

    /// GPU usage query (if applicable)
    pub gpu_usage: Option<String>,

    /// Network RX query
    pub network_rx: String,

    /// Network TX query
    pub network_tx: String,

    /// Disk usage query
    pub disk_usage: String,

    /// Temperature query
    pub temperature: Option<String>,
}

/// Custom Prometheus queries for service metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceQueries {
    /// Service status query
    pub service_status: String,

    /// CPU usage query for services
    pub cpu_usage: String,

    /// Memory usage query for services
    pub memory_usage: String,

    /// Request rate query
    pub requests_per_sec: String,

    /// Response time query
    pub response_time: String,

    /// Error rate query
    pub error_rate: String,
}

/// Prometheus authentication configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrometheusAuth {
    /// Username for basic auth
    pub username: String,

    /// Password for basic auth
    pub password: String,

    /// Bearer token (alternative to basic auth)
    pub bearer_token: Option<String>,
}

/// Health check configuration for services
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckConfig {
    /// Enable/disable health checks
    pub enabled: bool,

    /// Health check interval in seconds
    pub interval_secs: u64,

    /// Health check timeout in seconds
    pub timeout_secs: u64,

    /// Number of consecutive failures before marking as unhealthy
    pub failure_threshold: u32,

    /// Individual service health check configurations
    pub services: Vec<ServiceHealthCheck>,
}

/// Individual service health check configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceHealthCheck {
    /// Service name (matches the name in metrics)
    pub name: String,

    /// Health check endpoint URL
    pub endpoint: String,

    /// HTTP method to use (GET, POST, etc.)
    pub method: String,

    /// Expected HTTP status code(s)
    pub expected_status: Vec<u16>,

    /// Custom headers to send with health check
    pub headers: Option<std::collections::HashMap<String, String>>,

    /// Request body (for POST requests)
    pub body: Option<String>,

    /// Enable/disable this specific health check
    pub enabled: bool,

    /// Health check timeout in seconds (overrides global)
    pub timeout_secs: Option<u64>,

    /// Custom response time threshold in milliseconds
    pub response_time_threshold_ms: Option<u64>,
}

/// Node monitoring configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeConfig {
    /// List of nodes to monitor
    pub nodes: Vec<NodeConfigEntry>,

    /// Default values for nodes not explicitly configured
    pub defaults: NodeDefaults,
}

/// Individual node configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeConfigEntry {
    /// Node name/identifier
    pub name: String,

    /// Node IP address or hostname
    pub address: String,

    /// Custom labels for this node
    pub labels: Option<std::collections::HashMap<String, String>>,

    /// Override default settings for this node
    pub overrides: Option<NodeDefaults>,
}

/// Default values for node configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeDefaults {
    /// Default node display name
    pub display_name: Option<String>,

    /// Default temperature unit (C, F)
    pub temperature_unit: String,

    /// Default network unit (MB/s, GB/s, etc.)
    pub network_unit: String,

    /// Whether to show GPU metrics
    pub show_gpu: bool,
}

/// UI configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    /// Refresh rate for the UI in milliseconds
    pub refresh_rate_ms: u64,

    /// Whether to show graphs
    pub show_graphs: bool,

    /// Whether to show service logs
    pub show_service_logs: bool,

    /// Whether to show health checks
    pub show_health_checks: bool,

    /// Maximum number of log lines to display
    pub max_log_lines: usize,

    /// Color scheme customization
    pub colors: Option<ColorConfig>,

    /// Layout configuration
    pub layout: LayoutConfig,
}

/// Color scheme configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColorConfig {
    /// Primary color (hex code)
    pub primary: Option<String>,

    /// Success color (hex code)
    pub success: Option<String>,

    /// Warning color (hex code)
    pub warning: Option<String>,

    /// Danger color (hex code)
    pub danger: Option<String>,

    /// Text color (hex code)
    pub text: Option<String>,

    /// Border color (hex code)
    pub border: Option<String>,
}

/// Layout configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayoutConfig {
    /// Split ratios for main layout [nodes, services]
    pub main_split: Vec<u16>,

    /// Split ratios for service panel [graphs, health, logs]
    pub service_split: Vec<u16>,

    /// Split ratios for node panel [specs, graphs]
    pub node_split: Vec<u16>,
}

/// Logging configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    /// Log level (trace, debug, info, warn, error)
    pub level: String,

    /// Whether to log to file
    pub log_to_file: bool,

    /// Log file path (relative to config directory)
    pub log_file: Option<String>,

    /// Whether to log health check results
    pub log_health_checks: bool,

    /// Whether to log Prometheus queries
    pub log_prometheus_queries: bool,

    /// Maximum log file size in MB
    pub max_file_size_mb: u64,

    /// Maximum number of log files to retain
    pub max_files: u32,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            general: GeneralConfig::default(),
            prometheus: PrometheusConfig::default(),
            health_checks: HealthCheckConfig::default(),
            nodes: NodeConfig::default(),
            ui: UiConfig::default(),
            logging: LoggingConfig::default(),
        }
    }
}

impl Default for GeneralConfig {
    fn default() -> Self {
        Self {
            update_interval_secs: 5,
            history_retention: 60,
            connection_timeout_secs: 10,
            fullscreen: false,
            theme: "default".to_string(),
        }
    }
}

impl Default for PrometheusConfig {
    fn default() -> Self {
        Self {
            url: "http://100.81.76.55:30090".to_string(),
            timeout_secs: 10,
            query_interval_secs: 5,
            node_queries: NodeQueries::default(),
            service_queries: ServiceQueries::default(),
            auth: None,
        }
    }
}

impl Default for NodeQueries {
    fn default() -> Self {
        Self {
            cpu_usage: "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)".to_string(),
            memory_usage: "((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)".to_string(),
            gpu_usage: None,
            network_rx: "irate(node_network_receive_bytes_total[5m]) / 1024 / 1024".to_string(),
            network_tx: "irate(node_network_transmit_bytes_total[5m]) / 1024 / 1024".to_string(),
            disk_usage: "((1 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"})) * 100)".to_string(),
            temperature: Some("node_hwmon_temp_celsius".to_string()),
        }
    }
}

impl Default for ServiceQueries {
    fn default() -> Self {
        Self {
            service_status: "up".to_string(),
            cpu_usage: "rate(container_cpu_usage_seconds_total[5m]) * 100".to_string(),
            memory_usage: "container_memory_usage_bytes / container_spec_memory_limit_bytes * 100".to_string(),
            requests_per_sec: "rate(container_http_requests_total[5m])".to_string(),
            response_time: "histogram_quantile(0.95, rate(container_http_request_duration_seconds_bucket[5m])) * 1000".to_string(),
            error_rate: "rate(container_http_requests_total{status=~\"5..\"}[5m]) / rate(container_http_requests_total[5m]) * 100".to_string(),
        }
    }
}

impl Default for HealthCheckConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            interval_secs: 30,
            timeout_secs: 5,
            failure_threshold: 3,
            services: vec![
                ServiceHealthCheck {
                    name: "n8n-0".to_string(),
                    endpoint: "http://100.81.76.55:30678/healthz".to_string(),
                    method: "GET".to_string(),
                    expected_status: vec![200],
                    headers: None,
                    body: None,
                    enabled: true,
                    timeout_secs: Some(5),
                    response_time_threshold_ms: Some(1000),
                },
                ServiceHealthCheck {
                    name: "postgres-0".to_string(),
                    endpoint: "http://100.81.76.55:30543/health".to_string(),
                    method: "GET".to_string(),
                    expected_status: vec![200],
                    headers: None,
                    body: None,
                    enabled: true,
                    timeout_secs: Some(5),
                    response_time_threshold_ms: Some(500),
                },
                ServiceHealthCheck {
                    name: "redis-0".to_string(),
                    endpoint: "http://100.81.76.55:30379/health".to_string(),
                    method: "GET".to_string(),
                    expected_status: vec![200],
                    headers: None,
                    body: None,
                    enabled: true,
                    timeout_secs: Some(3),
                    response_time_threshold_ms: Some(200),
                },
                ServiceHealthCheck {
                    name: "prometheus-0".to_string(),
                    endpoint: "http://100.81.76.55:30090/-/healthy".to_string(),
                    method: "GET".to_string(),
                    expected_status: vec![200],
                    headers: None,
                    body: None,
                    enabled: true,
                    timeout_secs: Some(5),
                    response_time_threshold_ms: Some(500),
                },
                ServiceHealthCheck {
                    name: "grafana-0".to_string(),
                    endpoint: "http://100.81.76.55:30300/api/health".to_string(),
                    method: "GET".to_string(),
                    expected_status: vec![200],
                    headers: None,
                    body: None,
                    enabled: true,
                    timeout_secs: Some(5),
                    response_time_threshold_ms: Some(1000),
                },
            ],
        }
    }
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            nodes: vec![
                NodeConfigEntry {
                    name: "pesubuntu".to_string(),
                    address: "100.72.98.106".to_string(),
                    labels: Some({
                        let mut labels = std::collections::HashMap::new();
                        labels.insert("type".to_string(), "compute".to_string());
                        labels.insert("location".to_string(), "homelab".to_string());
                        labels
                    }),
                    overrides: Some(NodeDefaults {
                        display_name: Some("Compute Node".to_string()),
                        temperature_unit: "C".to_string(),
                        network_unit: "MB/s".to_string(),
                        show_gpu: true,
                    }),
                },
                NodeConfigEntry {
                    name: "asuna".to_string(),
                    address: "100.81.76.55".to_string(),
                    labels: Some({
                        let mut labels = std::collections::HashMap::new();
                        labels.insert("type".to_string(), "service".to_string());
                        labels.insert("location".to_string(), "homelab".to_string());
                        labels
                    }),
                    overrides: Some(NodeDefaults {
                        display_name: Some("Service Node".to_string()),
                        temperature_unit: "C".to_string(),
                        network_unit: "MB/s".to_string(),
                        show_gpu: false,
                    }),
                },
            ],
            defaults: NodeDefaults {
                display_name: None,
                temperature_unit: "C".to_string(),
                network_unit: "MB/s".to_string(),
                show_gpu: false,
            },
        }
    }
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            refresh_rate_ms: 250,
            show_graphs: true,
            show_service_logs: true,
            show_health_checks: true,
            max_log_lines: 10,
            colors: None,
            layout: LayoutConfig::default(),
        }
    }
}

impl Default for LayoutConfig {
    fn default() -> Self {
        Self {
            main_split: vec![50, 50], // 50% nodes, 50% services
            service_split: vec![40, 35, 25], // 40% graphs, 35% health, 25% logs
            node_split: vec![50, 50], // 50% specs, 50% graphs
        }
    }
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            level: "info".to_string(),
            log_to_file: false,
            log_file: Some("monitorium.log".to_string()),
            log_health_checks: true,
            log_prometheus_queries: false,
            max_file_size_mb: 10,
            max_files: 5,
        }
    }
}

impl Config {
    /// Load configuration from file or create default
    pub fn load() -> Result<Self> {
        let config_path = Self::get_config_path()?;

        if config_path.exists() {
            println!("Loading configuration from: {}", config_path.display());
            let content = fs::read_to_string(&config_path)
                .with_context(|| format!("Failed to read config file: {}", config_path.display()))?;

            let config: Config = serde_yaml::from_str(&content)
                .with_context(|| format!("Failed to parse config file: {}", config_path.display()))?;

            Ok(config)
        } else {
            println!("No configuration file found, creating default at: {}", config_path.display());
            let config = Config::default();
            config.save()?;
            Ok(config)
        }
    }

    /// Save configuration to file
    pub fn save(&self) -> Result<()> {
        let config_path = Self::get_config_path()?;

        // Create config directory if it doesn't exist
        if let Some(parent) = config_path.parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create config directory: {}", parent.display()))?;
        }

        let content = serde_yaml::to_string(self)
            .with_context(|| "Failed to serialize configuration")?;

        fs::write(&config_path, content)
            .with_context(|| format!("Failed to write config file: {}", config_path.display()))?;

        println!("Configuration saved to: {}", config_path.display());
        Ok(())
    }

    /// Get the configuration file path
    pub fn get_config_path() -> Result<PathBuf> {
        let home = home_dir().context("Could not find home directory")?;
        let config_dir = home.join(".monitorium");
        Ok(config_dir.join("config.yaml"))
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<()> {
        // Validate Prometheus URL
        if self.prometheus.url.is_empty() {
            return Err(anyhow::anyhow!("Prometheus URL cannot be empty"));
        }

        // Validate update intervals
        if self.general.update_interval_secs == 0 {
            return Err(anyhow::anyhow!("Update interval must be greater than 0"));
        }

        // Validate health check configurations
        for service in &self.health_checks.services {
            if service.enabled && service.endpoint.is_empty() {
                return Err(anyhow::anyhow!("Service {} has health check enabled but empty endpoint", service.name));
            }
        }

        Ok(())
    }
}