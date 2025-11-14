const { chromium } = require('playwright');

async function checkChartRendering() {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
      console.log('ERROR:', msg.text());
    }
  });

  page.on('pageerror', error => {
    errors.push(error.message);
    console.log('PAGE ERROR:', error.message);
  });

  await page.goto('https://assistant.homelab.pesulabs.net/dashboard', { waitUntil: 'networkidle' });
  
  // Wait for Chart.js to load
  await page.waitForTimeout(5000);

  // Check if Chart.js is loaded
  const chartJsLoaded = await page.evaluate(() => typeof Chart !== 'undefined');
  console.log('Chart.js loaded:', chartJsLoaded);

  // Check canvas element
  const canvasExists = await page.evaluate(() => {
    const canvas = document.getElementById('systemChart');
    return {
      exists: !!canvas,
      width: canvas?.width,
      height: canvas?.height,
      hasContext: !!canvas?.getContext('2d')
    };
  });
  console.log('Canvas state:', JSON.stringify(canvasExists, null, 2));

  // Check if chart instance exists
  const chartInstance = await page.evaluate(() => {
    const canvas = document.getElementById('systemChart');
    if (!canvas) return null;
    // Check if Chart.js chart is attached
    return {
      hasChart: !!window.systemChart,
      chartType: window.systemChart?.config?.type
    };
  });
  console.log('Chart instance:', JSON.stringify(chartInstance, null, 2));

  // Check for data
  const apiData = await page.evaluate(() => {
    return {
      healthData: window.healthData || null,
      lastUpdate: window.lastHealthUpdate || null
    };
  });
  console.log('API data:', JSON.stringify(apiData, null, 2));

  console.log('\nTotal errors:', errors.length);
  errors.forEach(err => console.log('  -', err));

  await browser.close();
}

checkChartRendering().catch(console.error);
