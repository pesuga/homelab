const { chromium } = require('playwright');
const fs = require('fs');

async function testDashboard() {
  console.log('🎭 Starting Family Assistant Dashboard Test...\n');

  const results = {
    timestamp: new Date().toISOString(),
    url: 'https://assistant.homelab.pesulabs.net/dashboard',
    pageLoadStatus: 'UNKNOWN',
    screenshotPath: null,
    consoleErrors: [],
    consoleWarnings: [],
    consoleLogs: [],
    visualElements: {},
    networkRequests: [],
    performance: {},
    memorySnapshots: [],
    systemPerformanceErrors: [],
    overallHealth: 'UNKNOWN'
  };

  let browser;
  try {
    // Launch browser with headless mode
    console.log('🚀 Launching browser...');
    browser = await chromium.launch({
      headless: true,
      args: ['--disable-dev-shm-usage', '--no-sandbox']
    });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      ignoreHTTPSErrors: true
    });
    const page = await context.newPage();

    // Capture console messages with detailed logging
    page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();
      const timestamp = new Date().toISOString();

      const logEntry = { text, type, timestamp };

      if (type === 'error') {
        results.consoleErrors.push(logEntry);
        console.log(`[${timestamp}] ❌ ERROR: ${text}`);

        // Check for System Performance related errors
        if (text.toLowerCase().includes('performance') ||
            text.toLowerCase().includes('chart') ||
            text.toLowerCase().includes('undefined') ||
            text.toLowerCase().includes('cannot read')) {
          results.systemPerformanceErrors.push(logEntry);
        }
      } else if (type === 'warning') {
        results.consoleWarnings.push(logEntry);
        console.log(`[${timestamp}] ⚠️  WARNING: ${text}`);
      } else {
        results.consoleLogs.push(logEntry);
      }
    });

    // Capture page errors
    page.on('pageerror', error => {
      const errorEntry = {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      };
      results.consoleErrors.push(errorEntry);
      console.error(`[${errorEntry.timestamp}] ❌ PAGE ERROR: ${error.message}`);
    });

    // Capture network requests
    page.on('response', response => {
      results.networkRequests.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
    });

    // Capture failed requests
    page.on('requestfailed', request => {
      const failInfo = {
        url: request.url(),
        failure: request.failure()?.errorText,
        timestamp: new Date().toISOString()
      };
      console.error(`[${failInfo.timestamp}] ❌ REQUEST FAILED: ${failInfo.url}`);
    });

    // Navigate to dashboard
    console.log('📍 Navigating to dashboard...');
    const startTime = Date.now();
    const response = await page.goto(results.url, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    const loadTime = Date.now() - startTime;

    results.performance.pageLoadTime = loadTime;
    results.pageLoadStatus = response.ok() ? 'SUCCESS' : `FAILED (${response.status()})`;
    console.log(`✅ Page loaded in ${loadTime}ms (status: ${response.status()})`);

    // Wait for initial data load (30 seconds as requested)
    console.log('⏳ Waiting 30 seconds for initial data load...');
    await page.waitForTimeout(30000);

    // Take initial screenshot
    console.log('📸 Taking initial screenshot...');
    const screenshotPath = '/tmp/dashboard-initial.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    results.screenshotPath = screenshotPath;

    // Check for System Performance widget specifically
    console.log('🔍 Looking for System Performance widget...');
    const perfWidget = await page.locator('text=System Performance').first();
    const perfWidgetCount = await perfWidget.count();
    results.visualElements.systemPerformanceWidget = {
      exists: perfWidgetCount > 0,
      count: perfWidgetCount
    };

    if (perfWidgetCount > 0) {
      console.log('✅ System Performance widget found');
      try {
        await perfWidget.screenshot({ path: '/tmp/system-performance-widget.png' });
        console.log('📸 System Performance widget screenshot saved');
      } catch (e) {
        console.log('⚠️  Could not capture widget screenshot:', e.message);
      }
    } else {
      console.log('❌ System Performance widget NOT found');
    }

    // Monitor memory usage for 60 seconds
    console.log('\n💾 Monitoring memory usage for 60 seconds...');
    for (let i = 0; i < 12; i++) {
      const metrics = await page.evaluate(() => {
        if (performance.memory) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (metrics) {
        const snapshot = {
          ...metrics,
          timestamp: new Date().toISOString(),
          elapsed: i * 5
        };
        results.memorySnapshots.push(snapshot);

        const usedMB = (metrics.usedJSHeapSize / 1024 / 1024).toFixed(2);
        const totalMB = (metrics.totalJSHeapSize / 1024 / 1024).toFixed(2);
        console.log(`  [${i * 5}s] Memory: ${usedMB} MB / ${totalMB} MB`);
      }

      if (i < 11) await page.waitForTimeout(5000);
    }

    // Take final screenshot
    console.log('\n📸 Taking final screenshot...');
    const screenshotPath2 = '/tmp/dashboard-final.png';
    await page.screenshot({ path: screenshotPath2, fullPage: true });
    results.screenshotAfterLoadPath = screenshotPath2;

    // Get page title and content
    results.pageTitle = await page.title();
    const bodyText = await page.textContent('body');
    results.hasContent = bodyText && bodyText.trim().length > 0;
    results.contentLength = bodyText ? bodyText.length : 0;

    // Calculate memory growth
    if (results.memorySnapshots.length > 0) {
      const firstMemory = results.memorySnapshots[0].usedJSHeapSize / 1024 / 1024;
      const lastMemory = results.memorySnapshots[results.memorySnapshots.length - 1].usedJSHeapSize / 1024 / 1024;
      const memoryGrowth = lastMemory - firstMemory;

      results.performance.memoryGrowth = {
        initial: firstMemory,
        final: lastMemory,
        growth: memoryGrowth,
        growthPercentage: ((memoryGrowth / firstMemory) * 100).toFixed(2),
        status: memoryGrowth > 50 ? 'HIGH' : 'OK'
      };

      console.log(`\n💾 MEMORY ANALYSIS:`);
      console.log(`  Initial: ${firstMemory.toFixed(2)} MB`);
      console.log(`  Final: ${lastMemory.toFixed(2)} MB`);
      console.log(`  Growth: ${memoryGrowth.toFixed(2)} MB (${results.performance.memoryGrowth.growthPercentage}%)`);
      console.log(`  Status: ${results.performance.memoryGrowth.status === 'HIGH' ? '⚠️  HIGH' : '✅ OK'}`);
    }

    // Analyze errors
    console.log('\n📊 SUMMARY:');
    console.log(`  Console Errors: ${results.consoleErrors.length}`);
    console.log(`  Console Warnings: ${results.consoleWarnings.length}`);
    console.log(`  System Performance Errors: ${results.systemPerformanceErrors.length}`);
    console.log(`  Page Load Time: ${results.performance.pageLoadTime}ms`);

    if (results.systemPerformanceErrors.length > 0) {
      console.log('\n⚠️  SYSTEM PERFORMANCE WIDGET ERRORS:');
      results.systemPerformanceErrors.forEach(err => {
        console.log(`  [${err.timestamp}] ${err.text || err.message}`);
      });
    }

    // Determine overall health
    const hasErrors = results.consoleErrors.length > 0;
    const pageLoaded = results.pageLoadStatus === 'SUCCESS';
    const hasContent = results.hasContent;

    if (pageLoaded && hasContent && !hasErrors) {
      results.overallHealth = 'HEALTHY';
    } else if (pageLoaded && hasContent) {
      results.overallHealth = 'DEGRADED';
    } else {
      results.overallHealth = 'UNHEALTHY';
    }

    console.log(`\n🏥 Overall Health: ${results.overallHealth}`);

    // Save detailed report
    const reportPath = '/tmp/dashboard-test-report.json';
    await fs.promises.writeFile(reportPath, JSON.stringify(results, null, 2));
    console.log(`\n📄 Detailed report saved to ${reportPath}`);
    console.log('\n📸 Screenshots saved:');
    console.log(`  - ${results.screenshotPath}`);
    console.log(`  - ${results.screenshotAfterLoadPath}`);

  } catch (error) {
    console.error('\n❌ TEST FAILED:', error.message);
    results.pageLoadStatus = 'FAILED';
    results.error = error.message;
    results.errorStack = error.stack;
    results.overallHealth = 'UNHEALTHY';

    try {
      await page.screenshot({ path: '/tmp/dashboard-error.png', fullPage: true });
      console.log('📸 Error screenshot saved to /tmp/dashboard-error.png');
    } catch (screenshotError) {
      console.error('Could not take error screenshot:', screenshotError.message);
    }
  } finally {
    if (browser) {
      await browser.close();
      console.log('✅ Browser closed');
    }
  }

  return results;
}

// Run the test
testDashboard().then(results => {
  console.log('\n' + '='.repeat(80));
  console.log('TEST RESULTS SUMMARY');
  console.log('='.repeat(80));
  console.log(`Status: ${results.overallHealth}`);
  console.log(`Errors: ${results.consoleErrors.length}`);
  console.log(`Warnings: ${results.consoleWarnings.length}`);
  console.log(`System Performance Errors: ${results.systemPerformanceErrors.length}`);
  if (results.performance.memoryGrowth) {
    console.log(`Memory Growth: ${results.performance.memoryGrowth.growth.toFixed(2)} MB (${results.performance.memoryGrowth.status})`);
  }
  console.log('='.repeat(80));

  process.exit(results.overallHealth === 'HEALTHY' ? 0 : 1);
}).catch(error => {
  console.error('\n❌ Test execution failed:', error);
  process.exit(1);
});
