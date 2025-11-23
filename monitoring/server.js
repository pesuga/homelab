#!/usr/bin/env node

const express = require('express');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const cors = require('cors');

const app = express();
const PORT = 8082;
const DASHBOARD_DIR = __dirname;
const LOGS_DIR = path.join(DASHBOARD_DIR, '../logs/metrics');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(DASHBOARD_DIR));

// Current model endpoint
app.get('/api/current-model', (req, res) => {
    try {
        const configPath = path.join(DASHBOARD_DIR, '../config/llamacpp.conf');
        const config = fs.readFileSync(configPath, 'utf8');
        const modelMatch = config.match(/^MODEL_NAME=(.+)$/m);
        const model = modelMatch ? modelMatch[1].trim() : 'Unknown';
        res.json({ model });
    } catch (error) {
        res.json({ model: 'Unknown' });
    }
});

// Metrics data endpoint
app.get('/api/metrics-data', (req, res) => {
    try {
        const csvPath = path.join(LOGS_DIR, 'metrics.csv');
        if (!fs.existsSync(csvPath)) {
            return res.json({ data: [] });
        }

        const csv = fs.readFileSync(csvPath, 'utf8');
        const lines = csv.trim().split('\n');

        if (lines.length < 2) {
            return res.json({ data: [] });
        }

        const headers = lines[0].split(',');
        const data = lines.slice(1).map(line => {
            const values = line.split(',');
            const obj = {};
            headers.forEach((header, index) => {
                obj[header] = values[index];
            });
            return obj;
        });

        res.json({ data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Benchmark endpoint
app.post('/api/benchmark', (req, res) => {
    const { prompt = 'Benchmark test', max_tokens = 50, iterations = 3 } = req.body;

    const scriptPath = path.join(DASHBOARD_DIR, '../scripts/llamacpp-metrics-collector.sh');
    const command = `${scriptPath} benchmark "current" "${prompt}" ${max_tokens} ${iterations}`;

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error('Benchmark error:', error);
            return res.status(500).json({ error: error.message });
        }

        // Parse benchmark results
        try {
            const lines = stdout.split('\n');
            const tpsMatch = lines.find(line => line.includes('Average tokens/sec:'));
            const tps = tpsMatch ? parseFloat(tpsMatch.split(':')[1].trim()) : 0;

            res.json({
                success: true,
                avg_tps: tps,
                prompt,
                max_tokens,
                iterations,
                output: stdout
            });
        } catch (parseError) {
            res.status(500).json({ error: 'Failed to parse benchmark results' });
        }
    });
});

// Get recent benchmarks
app.get('/api/benchmarks', (req, res) => {
    try {
        const logsDir = LOGS_DIR;
        if (!fs.existsSync(logsDir)) {
            return res.json({ benchmarks: [] });
        }

        const files = fs.readdirSync(logsDir)
            .filter(file => file.startsWith('benchmark_') && file.endsWith('.csv'))
            .sort()
            .reverse()
            .slice(0, 10); // Last 10 benchmarks

        const benchmarks = files.map(file => {
            const filePath = path.join(logsDir, file);
            const stats = fs.statSync(filePath);
            const content = fs.readFileSync(filePath, 'utf8');
            const lines = content.trim().split('\n');

            let avgTPS = 0;
            if (lines.length > 1) {
                const tpsValues = lines.slice(1).map(line => {
                    const values = line.split(',');
                    return parseFloat(values[6]) || 0;
                });
                avgTPS = tpsValues.reduce((a, b) => a + b, 0) / tpsValues.length;
            }

            return {
                file,
                timestamp: stats.mtime.toISOString(),
                avg_tps: avgTPS.toFixed(2),
                iterations: lines.length - 1
            };
        });

        res.json({ benchmarks });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    // Check if llama.cpp is accessible
    const axios = require('axios');
    axios.get('http://localhost:8081/health', { timeout: 5000 })
        .then(() => {
            res.json({ status: 'healthy', llama_cpp: true });
        })
        .catch(() => {
            res.json({ status: 'degraded', llama_cpp: false });
        });
});
// Prompt logging endpoint (privacy-preserving)
// Receives prompt text and duration (ms) and logs timestamp + duration only
app.post('/api/prompt-log', (req, res) => {
    const { prompt = '', duration_ms = 0 } = req.body;
    // Create a simple CSV line: timestamp,duration_ms
    const timestamp = new Date().toISOString();
    const line = `${timestamp},${duration_ms}\n`;
    const logPath = path.join(LOGS_DIR, 'prompt_log.csv');
    // Ensure header exists
    if (!fs.existsSync(logPath)) {
        fs.writeFileSync(logPath, 'timestamp,duration_ms\n');
    }
    fs.appendFileSync(logPath, line);
    res.json({ status: 'logged' });
});

// Retrieve prompt performance log (timestamp, duration, tokens, tps)
app.get('/api/prompt-performance', (req, res) => {
    const logPath = path.join(LOGS_DIR, 'prompt_performance.csv');
    if (!fs.existsSync(logPath)) {
        return res.json({ data: [] });
    }
    const csv = fs.readFileSync(logPath, 'utf8');
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',');
    const data = lines.slice(1).map(line => {
        const values = line.split(',');
        const obj = {};
        headers.forEach((h, i) => obj[h] = values[i]);
        return obj;
    });
    res.json({ data });
});

// System info endpoint
app.get('/api/system-info', async (req, res) => {
    try {
        // Get basic system info
        const os = require('os');
        const info = {
            hostname: os.hostname(),
            platform: os.platform(),
            arch: os.arch(),
            uptime: os.uptime(),
            loadavg: os.loadavg(),
            totalmem: os.totalmem(),
            freemem: os.freemem(),
            cpus: os.cpus().length
        };

        res.json(info);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 llama.cpp Monitoring Dashboard`);
    console.log(`====================================`);
    console.log(`📊 Dashboard: http://localhost:${PORT}/dashboard.html`);
    console.log(`🔗 API: http://localhost:${PORT}/api`);
    console.log(`💾 Logs: ${LOGS_DIR}`);
    console.log(``);
    console.log(`Commands to try:`);
    console.log(`  # Start metrics collection:`);
    console.log(`  ./scripts/llamacpp-metrics-collector.sh daemon 5`);
    console.log(``);
    console.log(`  # View real-time metrics:`);
    console.log(`  ./scripts/llamacpp-metrics-collector.sh monitor`);
    console.log(``);
    console.log(`  # Run benchmark:`);
    console.log(`  ./scripts/llamacpp-metrics-collector.sh benchmark`);
    console.log(``);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down monitoring server...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n👋 Shutting down monitoring server...');
    process.exit(0);
});