use std::io::{self, stdout};
use std::path::PathBuf;
use std::time::{Duration, Instant};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    Terminal,
};

mod app;
mod mock_data;
mod ui;
mod theme;
mod prometheus_client;
mod config;

use app::App;
use ui::ui;
use config::Config;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configuration
    let config = Config::load()
        .map_err(|e| format!("Failed to load configuration: {}", e))?;

    // Validate configuration
    config.validate()
        .map_err(|e| format!("Configuration validation failed: {}", e))?;

    println!("Monitorium starting with configuration from: {}", Config::get_config_path().unwrap_or_else(|_| PathBuf::from("unknown")).display());

    // setup terminal
    enable_raw_mode()?;
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // create app and run it
    let app = App::new_with_config(config).await?;
    let res = run_app(&mut terminal, app).await;

    // restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        println!("{err:?}");
    }

    Ok(())
}

async fn run_app<B: Backend>(terminal: &mut Terminal<B>, mut app: App) -> io::Result<()> {
    let mut last_tick = Instant::now();
    let mut last_prometheus_update = Instant::now();
    let tick_rate = Duration::from_millis(app.config.ui.refresh_rate_ms);
    let prometheus_update_rate = Duration::from_secs(app.config.prometheus.query_interval_secs);

    loop {
        terminal.draw(|f| ui(f, &app))?;

        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));

        if crossterm::event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Tab => app.switch_panel(),
                    KeyCode::Up => app.navigate_up(),
                    KeyCode::Down => app.navigate_down(),
                    KeyCode::Left => app.previous_service(),
                    KeyCode::Right => app.next_node(),
                    KeyCode::Char('r') => app.toggle_filter(),
                    KeyCode::Char(' ') => app.toggle_selection(),
                    KeyCode::Char('t') => app.next_theme(),
                    KeyCode::Char('T') => app.previous_theme(),
                    KeyCode::Char('h') | KeyCode::F(1) => return Ok(()), // Help/quit alternative
                    _ => {}
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            app.on_tick();
            last_tick = Instant::now();

            // Update Prometheus metrics less frequently
            if last_prometheus_update.elapsed() >= prometheus_update_rate {
                app.update_prometheus_metrics().await;
                last_prometheus_update = Instant::now();
            }
        }
    }
}
