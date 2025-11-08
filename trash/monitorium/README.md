# Monitorium - Homelab TUI Monitoring

A terminal-based monitoring dashboard for your homelab infrastructure, built with Rust and ratatui.

## Features

### Overview Tab
- **Node Summary**: Quick view of all nodes with CPU, Memory, and GPU usage
- **Service Summary**: Overview of all services with CPU, RPS, and latency
- **Resource Gauges**: Visual gauges for CPU, Memory, GPU, and Disk usage
- **Activity Sparklines**: Real-time sparkline charts for CPU and RPS history

### Nodes Tab
- **Node List**: Interactive list of all nodes with status and basic metrics
- **Node Details**: Detailed view including:
  - CPU, Memory, GPU, and Disk usage
  - Network I/O statistics
  - Temperature monitoring
  - Uptime information
  - IP addresses and status

### Services Tab
- **Service List**: Interactive list of all services with key metrics
- **Service Details**: Detailed view including:
  - CPU and Memory usage
  - Requests per second
  - Response time and error rates
  - Replica information
  - Uptime and namespace

### Compare Tab
- **Item Selection**: Select multiple nodes and services for comparison
- **Comparison Charts**: Side-by-side sparkline charts for CPU and Memory usage

## Keyboard Controls

### Navigation
- **Tab**: Switch to next tab (Overview → Nodes → Services → Compare)
- **Shift+Tab**: Switch to previous tab
- **↑/↓**: Navigate up/down in lists
- **←/→**: Navigate between nodes (when applicable)

### Actions
- **Space**: Select/deselect items for comparison
- **r**: Toggle filter mode
- **t**: Switch to next theme
- **T** (Shift+T): Switch to previous theme

### Application Control
- **q**: Quit the application
- **h**: Show help/quit (alternative to q)
- **F1**: Show help/quit (alternative to q)

## Theme System

Monitorium includes a comprehensive theme system with 9 popular terminal themes:

### Available Themes
1. **Default** - Classic cyan/blue color scheme
2. **Dracula** - Popular dark purple theme
3. **Gruvbox Dark** - Warm earth tones
4. **Nord** - Cool Nordic colors
5. **Solarized Dark** - Scientific color palette
6. **Cyberpunk** - Neon cyan/magenta aesthetic
7. **Monokai** - Classic dark theme
8. **One Dark** - VS Code inspired
9. **Tokyo Night** - Modern dark aesthetic

### Theme Features
- **Full color customization**: All UI elements use theme colors
- **Real-time switching**: Change themes instantly without restart
- **Status indicator**: Current theme name shown in status bar
- **Consistent design**: All components follow theme color scheme

### Theme Controls
- **t**: Switch to next theme in the list
- **T** (Shift+T): Switch to previous theme
- Current theme is displayed in the status bar

## Mock Data

Currently uses mock data that simulates a two-node homelab setup:

### Nodes
- **pesubuntu**: Compute node with AMD RX 7800 XT GPU
- **asuna**: Service node running K3s

### Services
- N8n (workflow automation)
- PostgreSQL (database)
- Redis (cache)
- Prometheus (metrics)
- Grafana (visualization)
- Qdrant (vector database)
- Flowise (AI flows)

## Installation & Running

### Prerequisites
- Rust 1.70+
- Terminal that supports ANSI escape codes

### Build
```bash
cargo build --release
```

### Run
```bash
cargo run
```

Or use the release binary:
```bash
./target/release/monitorium
```

## Architecture

The application is structured into several modules:

- **main.rs**: Application entry point and main event loop
- **app.rs**: Application state and business logic
- **ui.rs**: All UI rendering and layout logic
- **mock_data.rs**: Mock data generation for testing

### Key Technologies
- **ratatui**: Terminal UI framework
- **crossterm**: Cross-platform terminal handling
- **tokio**: Async runtime (for future real-time data)

## Future Enhancements

### Phase 2: Real Data Integration
- Connect to actual Prometheus API
- Replace mock data with real metrics
- Add authentication and error handling

### Phase 3: Advanced Features
- Historical data browsing
- Alert management
- Configuration management
- Plugin system for custom metrics

### Phase 4: Production Features
- systemd service integration
- Configuration files
- Logging and debugging tools
- Performance optimizations

## Development

### Adding New Metrics

1. Update the mock data structures in `mock_data.rs`
2. Add UI elements in the appropriate render function in `ui.rs`
3. Update the app state management in `app.rs`

### Customizing the UI

The UI is highly modular. Each tab has its own render function, and complex layouts are built using ratatui's layout system.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.