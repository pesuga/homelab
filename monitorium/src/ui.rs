use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{
        Block, Borders, Cell, Gauge, List, ListItem, Paragraph, Sparkline, Table, Row,
    },
    Frame,
};

use crate::app::{App, ActivePanel};

pub fn ui(f: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(0), Constraint::Length(3)].as_ref())
        .split(f.area());

    render_title_bar(f, app, chunks[0]);
    render_main_content(f, app, chunks[1]);
    render_status_bar(f, app, chunks[2]);
}

fn render_title_bar(f: &mut Frame, app: &App, area: Rect) {
    let title_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Min(20), Constraint::Percentage(40), Constraint::Min(20)].as_ref())
        .split(area);

    let title = Paragraph::new("Monitorium")
        .style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme_colors.border))
                .title("Homelab Monitoring")
                .title_style(Style::default().fg(app.theme_colors.secondary).add_modifier(Modifier::BOLD))
                .title_alignment(Alignment::Center),
        );

    f.render_widget(title, title_chunks[0]);

    // Show current selections with active panel indicator
    let panel_indicator = match app.active_panel {
        crate::app::ActivePanel::Nodes => "▼",
        crate::app::ActivePanel::Services => "▼",
    };

    let selected_node = app.nodes.keys().nth(app.selected_node_index).map_or("None", |v| v);
    let selected_service = app.services.keys().nth(app.selected_service_index).map_or("None", |v| v);

    let selected_info = format!("{} Node: {} | Service: {}",
        panel_indicator,
        selected_node,
        selected_service
    );

    let info = Paragraph::new(selected_info)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme_colors.border)))
        .alignment(Alignment::Center);

    f.render_widget(info, title_chunks[1]);

    // Show active panel on the right
    let active_text = format!("Panel: {}", match app.active_panel {
        crate::app::ActivePanel::Nodes => "Nodes",
        crate::app::ActivePanel::Services => "Services",
    });

    let active_panel = Paragraph::new(active_text)
        .style(Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme_colors.border)))
        .alignment(Alignment::Center);

    f.render_widget(active_panel, title_chunks[2]);
}

fn render_status_bar(f: &mut Frame, app: &App, area: Rect) {
    let status_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Min(0), Constraint::Length(55)].as_ref())
        .split(area);

    let help_text = vec![
        Line::from(vec![
            Span::styled("q", Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD)),
            Span::raw(":quit "),
            Span::styled("Tab", Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD)),
            Span::raw(":panel "),
            Span::styled("↑↓", Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD)),
            Span::raw(":navigate "),
            Span::styled("t", Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD)),
            Span::raw(":theme"),
        ]),
    ];

    let help = Paragraph::new(help_text)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme_colors.border)));
    f.render_widget(help, status_chunks[0]);

    let connection_indicator = match app.connection_status {
        crate::app::ConnectionStatus::Connected => "🟢",
        crate::app::ConnectionStatus::Disconnected(_) => "🔴",
        crate::app::ConnectionStatus::Connecting => "🟡",
    };

    let status_text = vec![Line::from(vec![
        Span::raw(format!("{} Prometheus | Tick: {} | Theme: {}",
            connection_indicator,
            app.tick_count,
            app.current_theme.name()
        ))
    ])];

    let status = Paragraph::new(status_text)
        .style(Style::default().fg(app.theme_colors.text_muted))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme_colors.border)))
        .alignment(Alignment::Right);
    f.render_widget(status, status_chunks[1]);
}

fn render_main_content(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Left panel - Nodes
    render_nodes_panel(f, app, chunks[0]);

    // Right panel - Services (filtered by selected node)
    render_services_panel(f, app, chunks[1]);
}

fn render_nodes_panel(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Top half: Node list + Hardware specs
    let top_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(60), Constraint::Percentage(40)].as_ref())
        .split(chunks[0]);

    render_nodes_table(f, app, top_chunks[0]);
    render_selected_node_details(f, app, top_chunks[1]);

    // Bottom half: Expanded graphs (50% of column)
    render_activity_sparklines(f, app, chunks[1]);
}

fn render_nodes_table(f: &mut Frame, app: &App, area: Rect) {
    let header_cells = ["Node", "Status", "CPU", "Memory", "GPU", "Disk", "Network", "Temp"]
        .iter()
        .map(|h| {
            Cell::from(*h)
                .style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
        });

    let header = Row::new(header_cells)
        .style(Style::default().bg(app.theme_colors.border))
        .height(1);

    let rows = app.nodes.iter().enumerate().map(|(i, (name, node))| {
        let is_selected = i == app.selected_node_index;
        let is_active_panel = app.active_panel == ActivePanel::Nodes;

        let cpu_color = if node.cpu_usage > 80.0 { app.theme_colors.gauge_danger }
                        else if node.cpu_usage > 60.0 { app.theme_colors.gauge_warning }
                        else { app.theme_colors.gauge_good };

        let mem_color = if node.memory_usage > 80.0 { app.theme_colors.gauge_danger }
                        else if node.memory_usage > 60.0 { app.theme_colors.gauge_warning }
                        else { app.theme_colors.gauge_good };

        let gpu_color = if node.gpu_usage > 80.0 { app.theme_colors.gauge_danger }
                        else if node.gpu_usage > 60.0 { app.theme_colors.gauge_warning }
                        else { app.theme_colors.gauge_good };

        let disk_color = if node.disk_usage > 80.0 { app.theme_colors.gauge_danger }
                         else if node.disk_usage > 60.0 { app.theme_colors.gauge_warning }
                         else { app.theme_colors.gauge_good };

        let temp_color = if node.temperature > 80.0 { app.theme_colors.gauge_danger }
                         else if node.temperature > 60.0 { app.theme_colors.gauge_warning }
                         else { app.theme_colors.gauge_good };

        let data_source = match app.connection_status {
            crate::app::ConnectionStatus::Connected => "🔴",
            _ => "📊", // Mock data indicator
        };

        let cells = vec![
            Cell::from(if is_selected && is_active_panel { format!("► {} {}", name, data_source) } else { format!("{} {}", name, data_source) }),
            Cell::from(node.status.clone()),
            Cell::from(format!("{:.1}%", node.cpu_usage)).style(Style::default().fg(cpu_color)),
            Cell::from(format!("{:.1}%", node.memory_usage)).style(Style::default().fg(mem_color)),
            Cell::from(if node.gpu_usage > 0.0 { format!("{:.1}%", node.gpu_usage) } else { "N/A".to_string() })
                .style(Style::default().fg(gpu_color)),
            Cell::from(format!("{:.1}%", node.disk_usage)).style(Style::default().fg(disk_color)),
            Cell::from(format!("↓{:.0} ↑{:.0}MB/s", node.network_rx, node.network_tx)),
            Cell::from(format!("{:.1}°C", node.temperature)).style(Style::default().fg(temp_color)),
        ];

        let style = if is_selected && is_active_panel {
            Style::default().bg(app.theme_colors.highlight).add_modifier(Modifier::BOLD)
        } else {
            Style::default()
        };

        Row::new(cells).style(style)
    });

    let table = Table::new(rows, [Constraint::Min(14), Constraint::Min(8), Constraint::Min(6),
                                   Constraint::Min(7), Constraint::Min(6), Constraint::Min(6),
                                   Constraint::Min(12), Constraint::Min(7)])
        .header(header)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Nodes")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(if app.active_panel == ActivePanel::Nodes {
                    Style::default().fg(app.theme_colors.info)
                } else {
                    Style::default().fg(app.theme_colors.border)
                }),
        )
        .highlight_style(Style::default().add_modifier(Modifier::BOLD));

    f.render_widget(table, area);
}

fn render_node_resources(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(6), Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Selected node details
    render_selected_node_details(f, app, chunks[0]);

    // Resource usage gauges
    render_resource_gauges(f, app, chunks[1]);

    // History sparklines
    render_activity_sparklines(f, app, chunks[2]);
}

fn render_selected_node_details(f: &mut Frame, app: &App, area: Rect) {
    let node_names: Vec<String> = app.nodes.keys().cloned().collect();
    if node_names.is_empty() || app.selected_node_index >= node_names.len() {
        return;
    }

    let node_name = &node_names[app.selected_node_index];
    let node = &app.nodes[node_name];

    // Create compact hardware specs text
    let hardware_specs = vec![
        Line::from(vec![
            Span::styled("Node: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(format!("{} | {} ({}c/{}t)", node_name, node.cpu_model, node.cpu_cores, node.cpu_threads)),
        ]),
        Line::from(vec![
            Span::styled("RAM: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(format!("{:.0}GB | ", node.memory_total_gb)),
            Span::styled("GPU: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(&node.gpu_model),
        ]),
        Line::from(vec![
            Span::styled("Storage: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(format!("{:.0}GB | {:.1}°C | ", node.disk_total_gb, node.temperature)),
            Span::styled("Usage: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(format!("CPU {:.1}% | Mem {:.1}%", node.cpu_usage, node.memory_usage)),
        ]),
    ];

    let details = Paragraph::new(hardware_specs)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Hardware Specs")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        );

    f.render_widget(details, area);
}

fn render_resource_gauges(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Length(3),
            Constraint::Length(3),
            Constraint::Length(3),
            Constraint::Min(0),
        ].as_ref())
        .split(area);

    let node_names: Vec<String> = app.nodes.keys().cloned().collect();
    if node_names.is_empty() || app.selected_node_index >= node_names.len() {
        return;
    }

    let node = &app.nodes[&node_names[app.selected_node_index]];

    // CPU Usage
    let cpu_gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("CPU Usage").border_style(Style::default().fg(app.theme_colors.border)))
        .gauge_style(
            Style::default()
                .fg(if node.cpu_usage > 80.0 { app.theme_colors.gauge_danger } else if node.cpu_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                .bg(app.theme_colors.background)
                .add_modifier(Modifier::BOLD),
        )
        .label(format!("{:.1}%", node.cpu_usage))
        .ratio(node.cpu_usage / 100.0);
    f.render_widget(cpu_gauge, chunks[0]);

    // Memory Usage
    let memory_gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("Memory Usage").border_style(Style::default().fg(app.theme_colors.border)))
        .gauge_style(
            Style::default()
                .fg(if node.memory_usage > 80.0 { app.theme_colors.gauge_danger } else if node.memory_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                .bg(app.theme_colors.background)
                .add_modifier(Modifier::BOLD),
        )
        .label(format!("{:.1}%", node.memory_usage))
        .ratio(node.memory_usage / 100.0);
    f.render_widget(memory_gauge, chunks[1]);

    // GPU Usage (only for nodes with GPU)
    if node.gpu_memory_total > 0 {
        let gpu_gauge = Gauge::default()
            .block(Block::default().borders(Borders::ALL).title("GPU Usage").border_style(Style::default().fg(app.theme_colors.border)))
            .gauge_style(
                Style::default()
                    .fg(if node.gpu_usage > 80.0 { app.theme_colors.gauge_danger } else if node.gpu_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                    .bg(app.theme_colors.background)
                    .add_modifier(Modifier::BOLD),
            )
            .label(format!("{:.1}%", node.gpu_usage))
            .ratio(node.gpu_usage / 100.0);
        f.render_widget(gpu_gauge, chunks[2]);
    }

    // Disk Usage
    let disk_gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("Disk Usage").border_style(Style::default().fg(app.theme_colors.border)))
        .gauge_style(
            Style::default()
                .fg(if node.disk_usage > 80.0 { app.theme_colors.gauge_danger } else if node.disk_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                .bg(app.theme_colors.background)
                .add_modifier(Modifier::BOLD),
        )
        .label(format!("{:.1}%", node.disk_usage))
        .ratio(node.disk_usage / 100.0);
    f.render_widget(disk_gauge, chunks[3]);
}

fn render_activity_sparklines(f: &mut Frame, app: &App, area: Rect) {
    let node_names: Vec<String> = app.nodes.keys().cloned().collect();
    if node_names.is_empty() || app.selected_node_index >= node_names.len() {
        return;
    }

    let node_name = &node_names[app.selected_node_index];
    let node = &app.nodes[node_name];

    // Create two-column layout for better visualization
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Left column - CPU and Memory
    let left_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(chunks[0]);

    // Right column - Network graphs
    let right_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(chunks[1]);

    // Node CPU History - Enhanced visibility
    if let Some(history) = app.node_history.get(node_name) {
        if !history.is_empty() {
            // Create bar-style data for better visibility
            let cpu_data: Vec<u64> = history.iter().map(|&x| {
                // Convert to 0-20 range for better bar visibility
                (x * 0.2) as u64
            }).collect();

            let cpu_sparkline = Sparkline::default()
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(format!("CPU Usage ({}%)", node.cpu_usage as u32))
                        .title_style(Style::default().fg(app.theme_colors.primary))
                        .border_style(Style::default().fg(app.theme_colors.border)),
                )
                .data(&cpu_data)
                .style(Style::default().fg(app.theme_colors.success))
                .max(20); // Max 100% * 0.2 = 20
            f.render_widget(cpu_sparkline, left_chunks[0]);
        } else {
            // Show current usage as a simple bar when no history
            let current_cpu = (node.cpu_usage * 0.2) as u64;
            let cpu_data = vec![current_cpu];
            let cpu_sparkline = Sparkline::default()
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(format!("CPU Usage ({}%)", node.cpu_usage as u32))
                        .title_style(Style::default().fg(app.theme_colors.primary))
                        .border_style(Style::default().fg(app.theme_colors.border)),
                )
                .data(&cpu_data)
                .style(Style::default().fg(app.theme_colors.success))
                .max(20);
            f.render_widget(cpu_sparkline, left_chunks[0]);
        }
    } else {
        // Show placeholder when no history exists yet
        let placeholder = Paragraph::new(format!("CPU: {:.1}% | Initializing...", node.cpu_usage))
            .style(Style::default().fg(app.theme_colors.text_muted))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("CPU Usage")
                    .title_style(Style::default().fg(app.theme_colors.primary))
                    .border_style(Style::default().fg(app.theme_colors.border)),
            );
        f.render_widget(placeholder, left_chunks[0]);
    }

    // Memory usage with better visibility
    let memory_data: Vec<u64> = (0..30).map(|i| {
        let base = app.nodes[node_name].memory_usage;
        // Add some variation to simulate memory fluctuations
        let variation = (i as f64 * 0.1).sin() * 3.0;
        ((base + variation).max(0.0).min(100.0) * 0.2) as u64 // Scale to 0-20 range
    }).collect();

    let memory_sparkline = Sparkline::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(format!("Memory Usage ({}%)", node.memory_usage as u32))
                .title_style(Style::default().fg(app.theme_colors.info))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .data(&memory_data)
        .style(Style::default().fg(app.theme_colors.info))
        .max(20); // Max 100% * 0.2 = 20
    f.render_widget(memory_sparkline, left_chunks[1]);

    // Network TX (outbound) with better visibility and correct values
    let network_tx_base = app.nodes[node_name].network_tx;

    let network_tx_text = Paragraph::new(vec![
        Line::from(Span::styled("Network Status", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))),
        Line::from(vec![]),
        Line::from(vec![
            Span::styled("↑ TX: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{:.1} MB/s", network_tx_base), Style::default().fg(app.theme_colors.warning).add_modifier(Modifier::BOLD))
        ]),
        Line::from(vec![
            Span::styled("↓ RX: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{:.1} MB/s", node.network_rx), Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
        ]),
        Line::from(vec![]),
        Line::from(Span::styled("Real-time network I/O", Style::default().fg(app.theme_colors.text_muted))),
    ])
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Network")
                .title_style(Style::default().fg(app.theme_colors.primary))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });
    f.render_widget(network_tx_text, right_chunks[0]);

    // Additional node info or empty placeholder
    let additional_info = Paragraph::new(vec![
        Line::from(Span::styled("System Info", Style::default().fg(app.theme_colors.info).add_modifier(Modifier::BOLD))),
        Line::from(vec![]),
        Line::from(vec![
            Span::styled("Disk: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{:.1}%", node.disk_usage), Style::default().fg(app.theme_colors.info))
        ]),
        Line::from(vec![
            Span::styled("Temp: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{:.1}°C", node.temperature), Style::default().fg(app.theme_colors.gauge_warning))
        ]),
        Line::from(vec![]),
        Line::from(Span::styled("Hardware monitoring", Style::default().fg(app.theme_colors.text_muted))),
    ])
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Hardware")
                .title_style(Style::default().fg(app.theme_colors.info))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });
    f.render_widget(additional_info, right_chunks[1]);
}

fn render_services_panel(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Top 50%: Services table
    render_services_table(f, app, chunks[0]);

    // Bottom 50%: Service graphs, health, and logs
    let service_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(40), Constraint::Percentage(35), Constraint::Percentage(25)].as_ref())
        .split(chunks[1]);

    render_service_activity_sparklines(f, app, service_chunks[0]);
    render_service_health_info(f, app, service_chunks[1]);
    render_service_logs(f, app, service_chunks[2]);
}

fn render_service_health_info(f: &mut Frame, app: &App, area: Rect) {
    // Get selected service using the same sorting as the services table
    let mut filtered_services: Vec<_> = app.services
        .iter()
        .filter(|(_name, service)| {
            // Show all homelab services
            service.namespace == "homelab"
        })
        .collect();

    // Sort alphabetically by service name - same as services table
    filtered_services.sort_by(|(name_a, _), (name_b, _)| name_a.cmp(name_b));

    if filtered_services.is_empty() || app.selected_service_index >= filtered_services.len() {
        let placeholder = Paragraph::new("No service selected")
            .style(Style::default().fg(app.theme_colors.text_muted))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Health Check")
                    .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                    .border_style(Style::default().fg(app.theme_colors.border)),
            );
        f.render_widget(placeholder, area);
        return;
    }

    let (service_name, service) = &filtered_services[app.selected_service_index];
    render_service_health(f, app, service_name, service, area);
}

fn render_service_activity_sparklines(f: &mut Frame, app: &App, area: Rect) {
    // Get selected service
    let service_names: Vec<String> = app.services.keys().cloned().collect();
    if service_names.is_empty() || app.selected_service_index >= service_names.len() {
        let placeholder = Paragraph::new("No services available")
            .style(Style::default().fg(app.theme_colors.text_muted))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Service Metrics")
                    .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                    .border_style(Style::default().fg(app.theme_colors.border)),
            );
        f.render_widget(placeholder, area);
        return;
    }

    let service_name = &service_names[app.selected_service_index];
    let service = &app.services[service_name];

    // Create two-column layout for service graphs
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Service CPU History with improved visibility
    if let Some(history) = app.service_history.get(service_name) {
        if !history.is_empty() {
            // Use same scaling as nodes for consistency
            let cpu_data: Vec<u64> = history.iter().map(|&x| (x * 0.2) as u64).collect();
            let cpu_sparkline = Sparkline::default()
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(format!("CPU Usage ({}%)", service.cpu_usage as u32))
                        .title_style(Style::default().fg(app.theme_colors.primary))
                        .border_style(Style::default().fg(app.theme_colors.border)),
                )
                .data(&cpu_data)
                .style(Style::default().fg(app.theme_colors.success))
                .max(20); // Max 100% * 0.2 = 20
            f.render_widget(cpu_sparkline, chunks[0]);
        } else {
            // Show current usage as bar when no history
            let current_cpu = (service.cpu_usage * 0.2) as u64;
            let cpu_data = vec![current_cpu];
            let cpu_sparkline = Sparkline::default()
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(format!("CPU Usage ({}%)", service.cpu_usage as u32))
                        .title_style(Style::default().fg(app.theme_colors.primary))
                        .border_style(Style::default().fg(app.theme_colors.border)),
                )
                .data(&cpu_data)
                .style(Style::default().fg(app.theme_colors.success))
                .max(20);
            f.render_widget(cpu_sparkline, chunks[0]);
        }
    } else {
        let placeholder = Paragraph::new(format!("CPU: {:.1}% | Initializing...", service.cpu_usage))
            .style(Style::default().fg(app.theme_colors.text_muted))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("CPU Usage")
                    .title_style(Style::default().fg(app.theme_colors.primary))
                    .border_style(Style::default().fg(app.theme_colors.border)),
            );
        f.render_widget(placeholder, chunks[0]);
    }

    // Service Memory with improved visibility
    let memory_data: Vec<u64> = (0..30).map(|i| {
        let base = service.memory_usage;
        let variation = (i as f64 * 0.1).sin() * 2.0;
        ((base + variation).max(0.0).min(100.0) * 0.2) as u64 // Scale to 0-20 range
    }).collect();

    let memory_sparkline = Sparkline::default()
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(format!("Memory Usage ({}%)", service.memory_usage as u32))
                .title_style(Style::default().fg(app.theme_colors.info))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .data(&memory_data)
        .style(Style::default().fg(app.theme_colors.info))
        .max(20); // Max 100% * 0.2 = 20
    f.render_widget(memory_sparkline, chunks[1]);
}

fn render_service_logs(f: &mut Frame, app: &App, area: Rect) {
    // Get selected service using the same sorting as the services table
    let mut filtered_services: Vec<_> = app.services
        .iter()
        .filter(|(_name, service)| {
            // Show all homelab services
            service.namespace == "homelab"
        })
        .collect();

    // Sort alphabetically by service name - same as services table
    filtered_services.sort_by(|(name_a, _), (name_b, _)| name_a.cmp(name_b));

    if filtered_services.is_empty() || app.selected_service_index >= filtered_services.len() {
        let placeholder = Paragraph::new("No services available")
            .style(Style::default().fg(app.theme_colors.text_muted))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Service Logs")
                    .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                    .border_style(Style::default().fg(app.theme_colors.border)),
            );
        f.render_widget(placeholder, area);
        return;
    }

    let (service_name, service) = &filtered_services[app.selected_service_index];

    // Create realistic log content based on service status
    let log_content = if service.status != "Running" {
        vec![
            Line::from(Span::styled("🔴 Service Error Logs", Style::default().fg(app.theme_colors.gauge_danger).add_modifier(Modifier::BOLD))),
            Line::from(vec![]),
            Line::from(Span::styled("ERROR", Style::default().fg(app.theme_colors.gauge_danger).add_modifier(Modifier::BOLD)))
                .spans(vec![Span::raw(format!(" [{}] Container failed to start", (app.tick_count / 4) % 24))]),
            Line::from(Span::styled("ERROR", Style::default().fg(app.theme_colors.gauge_danger).add_modifier(Modifier::BOLD)))
                .spans(vec![Span::raw(format!(" [{}] Pod crash loop back off", ((app.tick_count / 4) + 1) % 24))]),
            Line::from(Span::styled("WARN ", Style::default().fg(app.theme_colors.gauge_warning).add_modifier(Modifier::BOLD)))
                .spans(vec![Span::raw(format!(" [{}] Liveness probe failed", ((app.tick_count / 4) + 2) % 24))]),
            Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                .spans(vec![Span::raw(format!(" [{}] Attempting restart...", ((app.tick_count / 4) + 3) % 24))]),
        ]
    } else {
        // Simulate different types of logs for different services
        match service_name {
            name if name.contains("n8n") => vec![
                Line::from(Span::styled("🟢 n8n Service Logs", Style::default().fg(app.theme_colors.success).add_modifier(Modifier::BOLD))),
                Line::from(vec![]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] n8n started successfully", (app.tick_count / 4) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Database connected", ((app.tick_count / 4) + 1) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Webhook server listening on :5678", ((app.tick_count / 4) + 2) % 24))]),
                Line::from(Span::styled("WARN ", Style::default().fg(app.theme_colors.gauge_warning)))
                    .spans(vec![Span::raw(format!(" [{}] Rate limit approaching threshold", ((app.tick_count / 4) + 3) % 24))]),
            ],
            name if name.contains("postgres") => vec![
                Line::from(Span::styled("🟢 PostgreSQL Service Logs", Style::default().fg(app.theme_colors.success).add_modifier(Modifier::BOLD))),
                Line::from(vec![]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Database system is ready to accept connections", (app.tick_count / 4) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Autovacuum launched", ((app.tick_count / 4) + 1) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Checkpoint complete", ((app.tick_count / 4) + 2) % 24))]),
            ],
            name if name.contains("redis") => vec![
                Line::from(Span::styled("🟢 Redis Service Logs", Style::default().fg(app.theme_colors.success).add_modifier(Modifier::BOLD))),
                Line::from(vec![]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Server started", (app.tick_count / 4) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Ready to accept connections", ((app.tick_count / 4) + 1) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Background saving started", ((app.tick_count / 4) + 2) % 24))]),
            ],
            _ => vec![
                Line::from(Span::styled(format!("🟢 {} Service Logs", service_name), Style::default().fg(app.theme_colors.success).add_modifier(Modifier::BOLD))),
                Line::from(vec![]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Service started", (app.tick_count / 4) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Health check passed", ((app.tick_count / 4) + 1) % 24))]),
                Line::from(Span::styled("INFO ", Style::default().fg(app.theme_colors.text_muted)))
                    .spans(vec![Span::raw(format!(" [{}] Ready to serve requests", ((app.tick_count / 4) + 2) % 24))]),
            ],
        }
    };

    let logs_widget = Paragraph::new(log_content)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Service Logs")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });

    f.render_widget(logs_widget, area);
}

fn render_services_table(f: &mut Frame, app: &App, area: Rect) {
    let header_cells = ["Service", "Namespace", "Status", "CPU", "Memory", "RPS", "Latency", "Error", "Replicas"]
        .iter()
        .map(|h| {
            Cell::from(*h)
                .style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
        });

    let header = Row::new(header_cells)
        .style(Style::default().bg(app.theme_colors.border))
        .height(1);

    // Sort services alphabetically by name for consistent ordering
    let mut filtered_services: Vec<_> = app.services
        .iter()
        .filter(|(_name, service)| {
            // Show all homelab services
            service.namespace == "homelab"
        })
        .collect();

    // Sort alphabetically by service name but maintain selection stability
    filtered_services.sort_by(|(name_a, _), (name_b, _)| name_a.cmp(name_b));

    // Convert to indexed format for selection tracking
    let indexed_services: Vec<_> = filtered_services.into_iter().enumerate().collect();

    let rows = indexed_services.iter().map(|(i, (name, service))| {
        let is_selected = *i == app.selected_service_index;
        let is_active_panel = app.active_panel == ActivePanel::Services;

        let cpu_color = if service.cpu_usage > 50.0 { app.theme_colors.gauge_danger }
                        else if service.cpu_usage > 30.0 { app.theme_colors.gauge_warning }
                        else { app.theme_colors.gauge_good };

        let mem_color = if service.memory_usage > 75.0 { app.theme_colors.gauge_danger }
                        else if service.memory_usage > 50.0 { app.theme_colors.gauge_warning }
                        else { app.theme_colors.gauge_good };

        let rps_color = if service.requests_per_sec > 150.0 { app.theme_colors.gauge_danger }
                       else if service.requests_per_sec > 100.0 { app.theme_colors.gauge_warning }
                       else { app.theme_colors.gauge_good };

        let latency_color = if service.response_time > 300.0 { app.theme_colors.gauge_danger }
                           else if service.response_time > 200.0 { app.theme_colors.gauge_warning }
                           else { app.theme_colors.gauge_good };

        let error_color = if service.error_rate > 1.0 { app.theme_colors.gauge_danger }
                         else if service.error_rate > 0.5 { app.theme_colors.gauge_warning }
                         else { app.theme_colors.gauge_good };

        let status_color = if service.status == "Running" { app.theme_colors.success }
                          else { app.theme_colors.error };

        let replica_status = if service.ready_replicas == service.replicas { app.theme_colors.success }
                           else { app.theme_colors.warning };

        let cells = vec![
            Cell::from(if is_selected && is_active_panel { format!("► {}", name) } else { name.to_string() }),
            Cell::from(service.namespace.clone()),
            Cell::from(service.status.clone()).style(Style::default().fg(status_color)),
            Cell::from(format!("{:.1}%", service.cpu_usage)).style(Style::default().fg(cpu_color)),
            Cell::from(format!("{:.1}%", service.memory_usage)).style(Style::default().fg(mem_color)),
            Cell::from(format!("{:.1}", service.requests_per_sec)).style(Style::default().fg(rps_color)),
            Cell::from(format!("{:.0}ms", service.response_time)).style(Style::default().fg(latency_color)),
            Cell::from(format!("{:.1}%", service.error_rate)).style(Style::default().fg(error_color)),
            Cell::from(format!("{}/{}", service.ready_replicas, service.replicas))
                .style(Style::default().fg(replica_status)),
        ];

        let style = if is_selected && is_active_panel {
            Style::default().bg(app.theme_colors.highlight).add_modifier(Modifier::BOLD)
        } else {
            Style::default()
        };

        Row::new(cells).style(style)
    });

    let table = Table::new(rows, [Constraint::Min(12), Constraint::Min(10), Constraint::Min(8),
                                   Constraint::Min(5), Constraint::Min(6), Constraint::Min(6),
                                   Constraint::Min(7), Constraint::Min(6), Constraint::Min(8)])
        .header(header)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Services")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(if app.active_panel == ActivePanel::Services {
                    Style::default().fg(app.theme_colors.info)
                } else {
                    Style::default().fg(app.theme_colors.border)
                }),
        )
        .highlight_style(Style::default().add_modifier(Modifier::BOLD));

    f.render_widget(table, area);
}

fn render_service_details(f: &mut Frame, app: &App, area: Rect) {
    let service_names: Vec<String> = app.services.keys().cloned().collect();
    if service_names.is_empty() || app.selected_service_index >= service_names.len() {
        return;
    }

    let service_name = &service_names[app.selected_service_index];
    let service = &app.services[service_name];

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(4), Constraint::Percentage(50), Constraint::Percentage(50)].as_ref())
        .split(area);

    // Selected service details
    render_selected_service_details(f, app, service_name, service, chunks[0]);

    // Pod metrics
    render_service_metrics(f, app, service, chunks[1]);

    // Health metrics
    render_service_health(f, app, service_name, service, chunks[2]);
}

fn render_service_details_extended(f: &mut Frame, app: &App, service_name: &str, service: &crate::mock_data::ServiceMetrics, area: Rect) {
    let details = vec![
        Line::from(vec![
            Span::styled("Service: ", Style::default().fg(app.theme_colors.primary)),
            Span::styled(service_name, Style::default().add_modifier(Modifier::BOLD).fg(app.theme_colors.foreground)),
        ]),
        Line::from(vec![
            Span::styled("Namespace: ", Style::default().fg(app.theme_colors.primary)),
            Span::styled(&service.namespace, Style::default().fg(app.theme_colors.foreground)),
        ]),
        Line::from(vec![
            Span::styled("Status: ", Style::default().fg(app.theme_colors.primary)),
            Span::styled(
                &service.status,
                if service.status == "Running" {
                    Style::default().fg(app.theme_colors.success)
                } else {
                    Style::default().fg(app.theme_colors.error)
                },
            ),
        ]),
        Line::from(""),
        Line::from(vec![
            Span::styled("CPU: ", Style::default().fg(app.theme_colors.primary)),
            Span::styled(format!("{:.1}%", service.cpu_usage), Style::default().fg(app.theme_colors.foreground)),
        ]),
        Line::from(vec![
            Span::styled("Memory: ", Style::default().fg(app.theme_colors.primary)),
            Span::styled(format!("{:.1}%", service.memory_usage), Style::default().fg(app.theme_colors.foreground)),
        ]),
    ];

    let details_widget = Paragraph::new(details)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Service Details")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });

    f.render_widget(details_widget, area);
}

fn render_selected_service_details(f: &mut Frame, app: &App, service_name: &str, service: &crate::mock_data::ServiceMetrics, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(0)].as_ref())
        .split(area);

    // Service summary
    let details_text = format!("{} | Namespace: {} | Status: {} | Replicas: {}/{} | CPU: {:.1}% | Memory: {:.1}%",
        service_name,
        service.namespace,
        service.status,
        service.ready_replicas,
        service.replicas,
        service.cpu_usage,
        service.memory_usage
    );

    let details = Paragraph::new(details_text)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Selected Service")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        );

    f.render_widget(details, chunks[0]);

    // Error logs or service status
    let log_content = if service.status != "Running" {
        vec![
            Line::from(Span::styled("Service Status: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))),
            Line::from(Span::styled(format!("  • Status: {}", service.status),
                if service.status == "Running" { Style::default().fg(app.theme_colors.success) }
                else { Style::default().fg(app.theme_colors.warning) })),
            Line::from(Span::styled(format!("  • Ready Replicas: {}/{}", service.ready_replicas, service.replicas),
                if service.ready_replicas == service.replicas { Style::default().fg(app.theme_colors.success) }
                else { Style::default().fg(app.theme_colors.warning) })),
            Line::from(Span::styled("  • Health Check: Failed", Style::default().fg(app.theme_colors.gauge_danger))),
            Line::from(vec![]),
            Line::from(Span::styled("Recent Errors:", Style::default().fg(app.theme_colors.gauge_danger).add_modifier(Modifier::BOLD))),
            Line::from(Span::styled("  [ERROR] Connection timeout to database", Style::default().fg(app.theme_colors.gauge_danger))),
            Line::from(Span::styled("  [WARN]  High memory usage detected", Style::default().fg(app.theme_colors.gauge_warning))),
            Line::from(Span::styled("  [ERROR] Failed to start pod: CrashLoopBackOff", Style::default().fg(app.theme_colors.gauge_danger))),
        ]
    } else {
        vec![
            Line::from(Span::styled("Service Status: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))),
            Line::from(Span::styled(format!("  • Status: {}", service.status), Style::default().fg(app.theme_colors.success))),
            Line::from(Span::styled(format!("  • Ready Replicas: {}/{}", service.ready_replicas, service.replicas), Style::default().fg(app.theme_colors.success))),
            Line::from(Span::styled("  • Health Check: OK", Style::default().fg(app.theme_colors.success))),
            Line::from(vec![]),
            Line::from(Span::styled("Recent Logs:", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))),
            Line::from(Span::styled("  [INFO] Service started successfully", Style::default().fg(app.theme_colors.text_muted))),
            Line::from(Span::styled("  [INFO] Health check passed", Style::default().fg(app.theme_colors.text_muted))),
            Line::from(Span::styled("  [INFO] Processing requests normally", Style::default().fg(app.theme_colors.text_muted))),
        ]
    };

    let logs_widget = Paragraph::new(log_content)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Service Logs & Status")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });

    f.render_widget(logs_widget, chunks[1]);
}

fn render_service_metrics(f: &mut Frame, app: &App, service: &crate::mock_data::ServiceMetrics, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(33), Constraint::Percentage(33), Constraint::Percentage(34)].as_ref())
        .split(area);

    // CPU Usage Gauge (real data)
    let cpu_gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("CPU Usage").border_style(Style::default().fg(app.theme_colors.border)))
        .gauge_style(
            Style::default()
                .fg(if service.cpu_usage > 80.0 { app.theme_colors.gauge_danger } else if service.cpu_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                .bg(app.theme_colors.background)
                .add_modifier(Modifier::BOLD),
        )
        .label(format!("{:.1}%", service.cpu_usage))
        .ratio(service.cpu_usage / 100.0);
    f.render_widget(cpu_gauge, chunks[0]);

    // Memory Usage Gauge
    let memory_gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("Memory Usage").border_style(Style::default().fg(app.theme_colors.border)))
        .gauge_style(
            Style::default()
                .fg(if service.memory_usage > 80.0 { app.theme_colors.gauge_danger } else if service.memory_usage > 60.0 { app.theme_colors.gauge_warning } else { app.theme_colors.gauge_good })
                .bg(app.theme_colors.background)
                .add_modifier(Modifier::BOLD),
        )
        .label(format!("{:.1}%", service.memory_usage))
        .ratio(service.memory_usage / 100.0);
    f.render_widget(memory_gauge, chunks[1]);

    // Service Status
    let status_text = vec![
        Line::from(vec![
            Span::styled("Status: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::styled(
                &service.status,
                if service.status == "Running" {
                    Style::default().fg(app.theme_colors.success).add_modifier(Modifier::BOLD)
                } else {
                    Style::default().fg(app.theme_colors.error).add_modifier(Modifier::BOLD)
                },
            ),
        ]),
        Line::from(vec![
            Span::styled("Replicas: ", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD)),
            Span::raw(format!("{}/{}", service.ready_replicas, service.replicas)),
        ]),
    ];

    let status_paragraph = Paragraph::new(status_text)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Service Info")
                .title_style(Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(app.theme_colors.border)),
        );
    f.render_widget(status_paragraph, chunks[2]);
}

fn render_service_health(f: &mut Frame, app: &App, service_name: &str, service: &crate::mock_data::ServiceMetrics, area: Rect) {
    // Get health status color based on health_status
    let (health_color, health_icon) = match service.health_status.as_str() {
        "Healthy" => (app.theme_colors.success, "✅"),
        "Degraded" => (app.theme_colors.gauge_warning, "⚠️"),
        "Unhealthy" => (app.theme_colors.gauge_danger, "❌"),
        _ => (app.theme_colors.text_muted, "❓"),
    };

    let health_content = vec![
        Line::from(Span::styled("Health Probe", Style::default().fg(app.theme_colors.primary).add_modifier(Modifier::BOLD))),
        Line::from(vec![]),
        Line::from(vec![
            Span::styled("Status: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{} {}", health_icon, service.health_status), Style::default().fg(health_color).add_modifier(Modifier::BOLD))
        ]),
        Line::from(vec![
            Span::styled("Response: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{:.1}ms", service.health_response_time), Style::default().fg(app.theme_colors.foreground))
        ]),
        Line::from(vec![
            Span::styled("Failures: ", Style::default().fg(app.theme_colors.text_muted)),
            Span::styled(format!("{}", service.consecutive_failures),
                if service.consecutive_failures > 0 { app.theme_colors.gauge_danger } else { app.theme_colors.success })
        ]),
        Line::from(vec![]),
        Line::from(Span::styled(format!("Endpoint: {}", service.health_endpoint),
            Style::default().fg(app.theme_colors.text_muted).add_modifier(Modifier::ITALIC))),
    ];

    let health_widget = Paragraph::new(health_content)
        .style(Style::default().fg(app.theme_colors.foreground))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Health Check")
                .title_style(Style::default().fg(health_color).add_modifier(Modifier::BOLD))
                .border_style(Style::default().fg(health_color)),
        )
        .wrap(ratatui::widgets::Wrap { trim: true });

    f.render_widget(health_widget, area);
}