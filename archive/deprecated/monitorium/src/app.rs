use std::collections::HashMap;
use crate::mock_data::{NodeMetrics, ServiceMetrics};
use crate::theme::{Theme, ThemeColors};
use crate::prometheus_client::{PrometheusClient, PrometheusConfig};
use crate::config::Config;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CurrentTab {
    Overview,
    Nodes,
    Services,
    Compare,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ActivePanel {
    Nodes,
    Services,
}

#[derive(Debug, Clone)]
pub struct FilterState {
    pub enabled: bool,
    pub selected_node: Option<String>,
    pub selected_namespace: Option<String>,
    pub selected_service: Option<String>,
}

impl FilterState {
    pub fn new() -> Self {
        Self {
            enabled: false,
            selected_node: None,
            selected_namespace: None,
            selected_service: None,
        }
    }
}

pub struct App {
    pub title: String,
    pub should_quit: bool,
    pub current_tab: CurrentTab,
    pub active_panel: ActivePanel,
    pub selected_node_index: usize,
    pub selected_service_index: usize,
    pub selected_item_index: usize,
    pub filter: FilterState,
    pub selected_items: Vec<String>,
    pub tick_count: u64,
    pub current_theme: Theme,
    pub theme_colors: ThemeColors,

    // Configuration
    pub config: Config,

    // Prometheus client
    pub prometheus_client: PrometheusClient,
    pub connection_status: ConnectionStatus,

    // Real-time data
    pub nodes: HashMap<String, NodeMetrics>,
    pub services: HashMap<String, ServiceMetrics>,
    pub node_history: HashMap<String, Vec<f64>>,
    pub service_history: HashMap<String, Vec<f64>>,
}

#[derive(Debug, Clone)]
pub enum ConnectionStatus {
    Connected,
    Disconnected(String),
    Connecting,
}

impl App {
    pub async fn new() -> anyhow::Result<Self> {
        let config = Config::load()?;
        Self::new_with_config(config).await
    }

    pub async fn new_with_config(config: Config) -> anyhow::Result<Self> {
        let theme = match config.general.theme.as_str() {
            "dark" => Theme::Dracula,
            "light" => Theme::SolarizedDark,
            "default" => Theme::Default,
            "dracula" => Theme::Dracula,
            "gruvbox" => Theme::GruvboxDark,
            "nord" => Theme::Nord,
            "solarized" => Theme::SolarizedDark,
            "cyberpunk" => Theme::Cyberpunk,
            "monokai" => Theme::Monokai,
            "onedark" => Theme::OneDark,
            "tokyo" => Theme::TokyoNight,
            _ => Theme::Default,
        };
        let theme_colors = ThemeColors::from_theme(theme);

        // Initialize Prometheus client
        let prometheus_config = PrometheusConfig {
            url: config.prometheus.url.clone(),
            timeout_secs: config.prometheus.timeout_secs,
            query_interval_secs: config.prometheus.query_interval_secs,
        };
        let mut prometheus_client = PrometheusClient::new(prometheus_config.clone())?;

        // Test connection and fall back to mock data if needed
        let (nodes, services, connection_status) = match prometheus_client.test_connection().await {
            Ok(true) => {
                // Connection successful, fetch initial data
                match prometheus_client.update_metrics().await {
                    Ok(_) => {
                        let nodes = prometheus_client.get_nodes().clone();
                        let services = prometheus_client.get_services().clone();
                        (nodes, services, ConnectionStatus::Connected)
                    }
                    Err(e) => {
                        eprintln!("Failed to fetch initial metrics: {}, falling back to mock data", e);
                        let (nodes, services) = crate::mock_data::generate_mock_metrics();
                        (nodes, services, ConnectionStatus::Disconnected(e.to_string()))
                    }
                }
            }
            Ok(false) => {
                eprintln!("Prometheus not responding, falling back to mock data");
                let (nodes, services) = crate::mock_data::generate_mock_metrics();
                (nodes, services, ConnectionStatus::Disconnected("No response".to_string()))
            }
            Err(e) => {
                eprintln!("Failed to connect to Prometheus: {}, falling back to mock data", e);
                let (nodes, services) = crate::mock_data::generate_mock_metrics();
                (nodes, services, ConnectionStatus::Disconnected(e.to_string()))
            }
        };

        Ok(Self {
            title: "Monitorium - Homelab Monitoring".to_string(),
            should_quit: false,
            current_tab: CurrentTab::Overview,
            active_panel: ActivePanel::Nodes,
            selected_node_index: 0,
            selected_service_index: 0,
            selected_item_index: 0,
            filter: FilterState::new(),
            selected_items: Vec::new(),
            tick_count: 0,
            current_theme: theme,
            theme_colors,
            config,
            prometheus_client,
            connection_status,
            node_history: HashMap::new(),
            service_history: HashMap::new(),
            nodes,
            services,
        })
    }

    pub fn on_tick(&mut self) {
        self.tick_count += 1;
        self.update_history();
    }

    pub async fn update_prometheus_metrics(&mut self) {
        // Try to update metrics from Prometheus
        match self.prometheus_client.update_metrics().await {
            Ok(updated) => {
                if updated {
                    // Successfully updated, update existing data while preserving structure
                    let new_nodes = self.prometheus_client.get_nodes();
                    let new_services = self.prometheus_client.get_services();

                    // Update values for existing nodes without changing order
                    for (name, new_node) in new_nodes.iter() {
                        if let Some(existing_node) = self.nodes.get_mut(name) {
                            // Update only the metrics, preserve hardware specs
                            existing_node.cpu_usage = new_node.cpu_usage;
                            existing_node.memory_usage = new_node.memory_usage;
                            existing_node.gpu_usage = new_node.gpu_usage;
                            existing_node.gpu_memory = new_node.gpu_memory;
                            existing_node.network_rx = new_node.network_rx;
                            existing_node.network_tx = new_node.network_tx;
                            existing_node.disk_usage = new_node.disk_usage;
                            existing_node.temperature = new_node.temperature;
                        }
                    }

                    // Update values for existing services without changing order
                    for (name, new_service) in new_services.iter() {
                        if let Some(existing_service) = self.services.get_mut(name) {
                            // Update only the metrics, preserve basic info
                            existing_service.cpu_usage = new_service.cpu_usage;
                            existing_service.memory_usage = new_service.memory_usage;
                            existing_service.requests_per_sec = new_service.requests_per_sec;
                            existing_service.response_time = new_service.response_time;
                            existing_service.error_rate = new_service.error_rate;
                            existing_service.status = new_service.status.clone();
                            existing_service.ready_replicas = new_service.ready_replicas;
                        }
                    }

                    self.connection_status = ConnectionStatus::Connected;
                }
            }
            Err(e) => {
                eprintln!("Failed to update Prometheus metrics: {}", e);
                self.connection_status = ConnectionStatus::Disconnected(e.to_string());

                // Fall back to mock data updates if Prometheus is disconnected
                self.update_mock_metrics();
            }
        }
    }

    fn update_mock_metrics(&mut self) {
        use rand::Rng;
        let mut rng = rand::thread_rng();

        // Only update mock metrics minimally to avoid graph jumping
        // Small changes for realistic variation but keep graphs mostly stable
        for node in self.nodes.values_mut() {
            // Much smaller ranges to keep graphs stable
            node.cpu_usage = (node.cpu_usage + rng.gen_range(-0.5..0.5)).clamp(10.0, 95.0);
            node.memory_usage = (node.memory_usage + rng.gen_range(-0.3..0.3)).clamp(20.0, 85.0);
            node.gpu_usage = (node.gpu_usage + rng.gen_range(-1.0..1.0)).clamp(0.0, 100.0);
            node.gpu_memory = (node.gpu_memory + rng.gen_range(-0.2..0.2)).clamp(30.0, 70.0);
            node.network_rx = (node.network_rx + rng.gen_range(-10.0..20.0)).clamp(0.0, 1000.0);
            node.network_tx = (node.network_tx + rng.gen_range(-8.0..15.0)).clamp(0.0, 800.0);
            node.disk_usage = (node.disk_usage + rng.gen_range(-0.1..0.1)).clamp(40.0, 90.0);
        }

        // Update service metrics with minimal changes
        for service in self.services.values_mut() {
            service.cpu_usage = (service.cpu_usage + rng.gen_range(-0.2..0.3)).clamp(0.5, 80.0);
            service.memory_usage = (service.memory_usage + rng.gen_range(-0.1..0.2)).clamp(10.0, 75.0);
            service.requests_per_sec = (service.requests_per_sec + rng.gen_range(-1.0..2.0)).clamp(0.0, 200.0);
            service.response_time = (service.response_time + rng.gen_range(-5.0..10.0)).clamp(50.0, 500.0);
            service.error_rate = (service.error_rate + rng.gen_range(-0.05..0.1)).clamp(0.0, 5.0);
        }
    }

    fn update_history(&mut self) {
        let max_history = self.config.general.history_retention;
        let update_interval = (1000 / self.config.ui.refresh_rate_ms) as u64; // Convert to ticks

        // Only update history at configured intervals
        if self.tick_count % update_interval != 0 {
            return;
        }

        for (node_name, node) in &self.nodes {
            let history = self.node_history.entry(node_name.clone()).or_insert_with(Vec::new);
            history.push(node.cpu_usage);
            if history.len() > max_history {
                history.remove(0);
            }
        }

        // For services, use CPU usage instead of fake RPS since we don't have real RPS data
        for (service_name, service) in &self.services {
            let history = self.service_history.entry(service_name.clone()).or_insert_with(Vec::new);
            history.push(service.cpu_usage);
            if history.len() > max_history {
                history.remove(0);
            }
        }
    }

    // Node navigation
    pub fn next_node(&mut self) {
        let node_count = self.nodes.len();
        if node_count > 0 {
            self.selected_node_index = (self.selected_node_index + 1) % node_count;
        }
    }

    pub fn previous_node(&mut self) {
        let node_count = self.nodes.len();
        if node_count > 0 {
            self.selected_node_index = if self.selected_node_index == 0 {
                node_count - 1
            } else {
                self.selected_node_index - 1
            };
        }
    }

    // Service navigation
    pub fn next_service(&mut self) {
        let service_count = self.services.len();
        if service_count > 0 {
            self.selected_service_index = (self.selected_service_index + 1) % service_count;
        }
    }

    pub fn previous_service(&mut self) {
        let service_count = self.services.len();
        if service_count > 0 {
            self.selected_service_index = if self.selected_service_index == 0 {
                service_count - 1
            } else {
                self.selected_service_index - 1
            };
        }
    }

    // Panel navigation
    pub fn switch_panel(&mut self) {
        match self.active_panel {
            ActivePanel::Nodes => self.active_panel = ActivePanel::Services,
            ActivePanel::Services => self.active_panel = ActivePanel::Nodes,
        }
    }

    // Navigation methods for active panel
    pub fn navigate_up(&mut self) {
        match self.active_panel {
            ActivePanel::Nodes => self.previous_node(),
            ActivePanel::Services => self.previous_service(),
        }
    }

    pub fn navigate_down(&mut self) {
        match self.active_panel {
            ActivePanel::Nodes => self.next_node(),
            ActivePanel::Services => self.next_service(),
        }
    }

    pub fn next_tab(&mut self) {
        let tabs = [CurrentTab::Overview, CurrentTab::Nodes, CurrentTab::Services, CurrentTab::Compare];
        let current_pos = tabs.iter().position(|&t| t == self.current_tab).unwrap_or(0);
        self.current_tab = tabs[(current_pos + 1) % tabs.len()];
    }

    pub fn previous_tab(&mut self) {
        let tabs = [CurrentTab::Overview, CurrentTab::Nodes, CurrentTab::Services, CurrentTab::Compare];
        let current_pos = tabs.iter().position(|&t| t == self.current_tab).unwrap_or(0);
        self.current_tab = tabs[(current_pos + tabs.len() - 1) % tabs.len()];
    }

    pub fn toggle_filter(&mut self) {
        self.filter.enabled = !self.filter.enabled;
    }

    pub fn toggle_selection(&mut self) {
        let items = match self.current_tab {
            CurrentTab::Nodes => self.nodes.keys().cloned().collect(),
            CurrentTab::Services => self.services.keys().cloned().collect(),
            _ => vec![],
        };

        if !items.is_empty() && self.selected_item_index < items.len() {
            let item = &items[self.selected_item_index];
            if let Some(pos) = self.selected_items.iter().position(|x| x == item) {
                self.selected_items.remove(pos);
            } else {
                self.selected_items.push(item.clone());
            }
        }
    }

    // Theme switching methods
    pub fn next_theme(&mut self) {
        self.current_theme = self.current_theme.next();
        self.theme_colors = ThemeColors::from_theme(self.current_theme);
    }

    pub fn previous_theme(&mut self) {
        self.current_theme = self.current_theme.previous();
        self.theme_colors = ThemeColors::from_theme(self.current_theme);
    }

    pub fn get_filtered_items(&self) -> Vec<String> {
        match self.current_tab {
            CurrentTab::Nodes => {
                let mut items: Vec<String> = self.nodes.keys().cloned().collect();
                if let Some(node_filter) = &self.filter.selected_node {
                    items.retain(|name| name.contains(node_filter));
                }
                items
            }
            CurrentTab::Services => {
                let mut items: Vec<String> = self.services.keys().cloned().collect();
                if let Some(namespace_filter) = &self.filter.selected_namespace {
                    items.retain(|name| {
                        self.services.get(name)
                            .map(|s| s.namespace.contains(namespace_filter))
                            .unwrap_or(false)
                    });
                }
                if let Some(service_filter) = &self.filter.selected_service {
                    items.retain(|name| name.contains(service_filter));
                }
                items
            }
            _ => vec![],
        }
    }
}