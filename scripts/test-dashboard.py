#!/usr/bin/env python3
"""
Family Assistant Dashboard Testing Script
Tests dashboard functionality using Playwright
"""

import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def test_dashboard():
    """Test the Family Assistant dashboard"""

    results = {
        'timestamp': datetime.now().isoformat(),
        'url': 'http://100.81.76.55:30801/dashboard',
        'pageLoadStatus': 'UNKNOWN',
        'screenshotPath': None,
        'consoleErrors': [],
        'consoleWarnings': [],
        'consoleLogs': [],
        'visualElements': {},
        'networkRequests': [],
        'performance': {},
        'overallHealth': 'UNKNOWN'
    }

    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # Capture console messages
            def handle_console(msg):
                msg_type = msg.type
                text = msg.text

                if msg_type == 'error':
                    results['consoleErrors'].append(text)
                elif msg_type == 'warning':
                    results['consoleWarnings'].append(text)
                else:
                    results['consoleLogs'].append(text)

            page.on('console', handle_console)

            # Capture network requests
            def handle_response(response):
                results['networkRequests'].append({
                    'url': response.url,
                    'status': response.status,
                    'statusText': response.status_text
                })

            page.on('response', handle_response)

            # Navigate to dashboard
            start_time = asyncio.get_event_loop().time()
            response = await page.goto(
                results['url'],
                wait_until='networkidle',
                timeout=30000
            )
            load_time = (asyncio.get_event_loop().time() - start_time) * 1000

            results['performance']['pageLoadTime'] = f"{load_time:.2f}ms"
            results['pageLoadStatus'] = 'SUCCESS' if response.ok else f"FAILED ({response.status})"

            # Wait for dynamic content
            await page.wait_for_timeout(2000)

            # Take screenshots
            screenshot_path = '/home/pesu/Rakuflow/systems/homelab/scripts/dashboard-screenshot.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            results['screenshotPath'] = screenshot_path

            # Check for key dashboard elements
            async def check_element(selector, name):
                try:
                    element = await page.query_selector(selector)
                    is_visible = await element.is_visible() if element else False
                    return {'exists': element is not None, 'visible': is_visible}
                except Exception as e:
                    return {'exists': False, 'visible': False, 'error': str(e)}

            # Check common dashboard elements
            results['visualElements'] = {
                'title': await check_element('h1, .dashboard-title, [class*="title"]', 'title'),
                'systemMetrics': await check_element('[class*="metric"], [class*="stats"], [class*="card"]', 'system metrics'),
                'serviceStatus': await check_element('[class*="service"], [class*="status"]', 'service status'),
                'charts': await check_element('canvas, svg', 'charts'),
                'websocket': await check_element('[class*="websocket"], [class*="realtime"], [class*="connection"]', 'websocket indicator'),
                'navigation': await check_element('nav, [class*="nav"]', 'navigation'),
                'footer': await check_element('footer', 'footer'),
                'container': await check_element('.container, [class*="container"]', 'container')
            }

            # Get page title
            results['pageTitle'] = await page.title()

            # Get page content
            body_text = await page.text_content('body')
            results['hasContent'] = body_text and len(body_text.strip()) > 0
            results['contentLength'] = len(body_text) if body_text else 0

            # Check for specific dashboard data
            try:
                metrics_text = body_text.lower() if body_text else ''
                results['containsMetrics'] = {
                    'cpu': 'cpu' in metrics_text,
                    'memory': 'memory' in metrics_text or 'ram' in metrics_text,
                    'disk': 'disk' in metrics_text or 'storage' in metrics_text,
                    'services': 'service' in metrics_text,
                    'homelab': 'homelab' in metrics_text,
                    'family': 'family' in metrics_text or 'assistant' in metrics_text
                }
            except Exception as e:
                results['containsMetrics'] = {'error': str(e)}

            # Check page structure
            try:
                html_content = await page.content()
                results['pageStructure'] = {
                    'hasHTML': '<html' in html_content,
                    'hasHead': '<head' in html_content,
                    'hasBody': '<body' in html_content,
                    'hasScript': '<script' in html_content,
                    'hasStyle': '<style' in html_content or 'stylesheet' in html_content
                }
            except Exception as e:
                results['pageStructure'] = {'error': str(e)}

            # Test responsiveness - wait and take another screenshot
            await page.wait_for_timeout(3000)

            screenshot_path2 = '/home/pesu/Rakuflow/systems/homelab/scripts/dashboard-screenshot-after-load.png'
            await page.screenshot(path=screenshot_path2, full_page=True)
            results['screenshotAfterLoadPath'] = screenshot_path2

            # Determine overall health
            has_errors = len(results['consoleErrors']) > 0
            page_loaded = results['pageLoadStatus'] == 'SUCCESS'
            has_content = results['hasContent']

            if page_loaded and has_content and not has_errors:
                results['overallHealth'] = 'HEALTHY'
            elif page_loaded and has_content:
                results['overallHealth'] = 'DEGRADED'
            else:
                results['overallHealth'] = 'UNHEALTHY'

            await browser.close()

        except Exception as e:
            results['pageLoadStatus'] = 'FAILED'
            results['error'] = str(e)
            results['overallHealth'] = 'UNHEALTHY'

    return results

# Run the test
if __name__ == '__main__':
    results = asyncio.run(test_dashboard())
    print(json.dumps(results, indent=2))
