"""PDF builder using screenshots of web pages.

This module captures screenshots of web pages and combines them into a PDF.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable, Union
from io import BytesIO
import asyncio

try:
    import aiohttp
except ImportError:
    aiohttp = None

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from PIL import Image
# Increase PIL's image size limit to handle high-resolution screenshots
# Default limit is ~178M pixels, we need higher for 5K screenshots with device_scale_factor=3
Image.MAX_IMAGE_PIXELS = 1_000_000_000  # 1 billion pixels limit
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, PageBreak, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor

from weekly_report.src.config import Config
from loguru import logger


async def capture_page_screenshot_with_retry(
    page: Page,
    url: str,
    wait_selector: Optional[str] = None,
    timeout: int = 60000,
    wait_for_network: bool = False,
    max_retries: int = 2
) -> bytes:
    """Capture a screenshot with retry logic.
    
    Args:
        page: Playwright Page object
        url: URL to navigate to
        wait_selector: CSS selector to wait for (optional)
        timeout: Maximum time to wait in milliseconds
        wait_for_network: Whether to wait for network to be idle (default False for faster loading)
        max_retries: Maximum number of retries (default 2)
    
    Returns:
        Screenshot bytes (PNG format)
    
    Raises:
        Exception: If screenshot capture fails after all retries
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"📸 Attempt {attempt + 1}/{max_retries + 1} to capture screenshot: {url}")
            screenshot = await capture_page_screenshot(
                page, url, wait_selector, timeout, wait_for_network
            )
            if attempt > 0:
                logger.info(f"✅ Screenshot captured successfully on retry attempt {attempt + 1}")
            else:
                logger.debug(f"✅ Screenshot captured successfully on first attempt")
            return screenshot
        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            logger.warning(f"⚠️ Screenshot capture attempt {attempt + 1} failed: {error_type}: {str(e)}")
            if attempt < max_retries:
                logger.info(f"⏳ Retrying in 2 seconds... (attempt {attempt + 2}/{max_retries + 1})")
                await asyncio.sleep(2)
            else:
                logger.error(f"❌ All {max_retries + 1} attempts failed for {url}")
                logger.error(f"   Last error: {error_type}: {str(e)}")
                import traceback
                logger.error(f"   Last error traceback: {traceback.format_exc()}")
                raise Exception(f"Failed to capture screenshot after {max_retries + 1} attempts: {str(e)}") from e
    
    # Should never reach here, but just in case
    if last_error:
        raise last_error
    raise Exception(f"Failed to capture screenshot after {max_retries + 1} attempts")


async def capture_page_screenshot(
    page: Page,
    url: str,
    wait_selector: Optional[str] = None,
    timeout: int = 60000,
    wait_for_network: bool = False
) -> bytes:
    """Capture a screenshot of a page after waiting for content to load.
    
    Args:
        page: Playwright Page object
        url: URL to navigate to
        wait_selector: CSS selector to wait for (optional)
        timeout: Maximum time to wait in milliseconds
        wait_for_network: Whether to wait for network to be idle (default False for faster loading)
    
    Returns:
        Screenshot bytes (PNG format)
    
    Raises:
        Exception: If screenshot capture fails
    """
    logger.info(f"Navigating to {url}")
    
    # CRITICAL: Disable Fast Refresh BEFORE navigating to prevent page reloads
    # This must be done before navigation to prevent Fast Refresh from interrupting
    try:
        # Navigate to a blank page first to set up the environment
        await page.goto("about:blank", wait_until='domcontentloaded', timeout=5000)
        
        # Set extra HTTP headers to prevent HMR
        try:
            await page.setExtraHTTPHeaders({
                'X-Requested-With': 'XMLHttpRequest',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            logger.debug("✅ Set extra HTTP headers to prevent HMR")
        except Exception as e:
            logger.warning(f"⚠️ Could not set extra HTTP headers: {e}")
        
        # Disable Fast Refresh and HMR before navigating to actual page
        await page.evaluate("""
            (function() {
                // Disable Next.js Fast Refresh
                if (window.__NEXT_DATA__) {
                    window.__NEXT_DATA__.dev = false;
                }
                // Disable HMR (Hot Module Replacement)
                if (window.__NEXT_HOT_RELOAD__) {
                    window.__NEXT_HOT_RELOAD__ = false;
                }
                // Prevent any WebSocket connections that might trigger refresh
                window.__NEXT_DISABLE_FAST_REFRESH = true;
                
                // Disable all WebSocket connections that might trigger Fast Refresh
                const originalWebSocket = window.WebSocket;
                window.WebSocket = function(...args) {
                    const ws = new originalWebSocket(...args);
                    // Only allow connections that aren't related to Fast Refresh
                    const originalSend = ws.send.bind(ws);
                    ws.send = function(data) {
                        if (typeof data === 'string' && (data.includes('fast-refresh') || data.includes('HMR'))) {
                            return; // Block Fast Refresh/HMR messages
                        }
                        return originalSend(data);
                    };
                    return ws;
                };
                
                // Block WebSocket connections more aggressively
                const originalAddEventListener = window.addEventListener;
                window.addEventListener = function(type, listener, options) {
                    if (type === 'message' && listener && listener.toString().includes('fast-refresh')) {
                        return; // Block Fast Refresh event listeners
                    }
                    return originalAddEventListener.call(this, type, listener, options);
                };
            })();
        """)
        logger.info("✅ Disabled Fast Refresh and HMR before navigation")
    except Exception as e:
        logger.warning(f"⚠️ Could not disable Fast Refresh before navigation: {e}")
        # Continue anyway - might still work
    
    # Use domcontentloaded for faster loading, then wait for specific selectors
    wait_until = 'networkidle' if wait_for_network else 'domcontentloaded'
    
    try:
        logger.info(f"Attempting to navigate to {url} with wait_until={wait_until}, timeout={timeout}ms")
        response = await page.goto(url, wait_until=wait_until, timeout=timeout)
        if response:
            logger.info(f"✅ Page loaded with status: {response.status}")
            if response.status >= 400:
                raise Exception(f"Page returned status {response.status} for {url}")
        else:
            logger.warning(f"⚠️ No response received for {url}, continuing anyway...")
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ Navigation error for {url}: {error_type}: {str(e)}")
        import traceback
        logger.error(f"Navigation traceback: {traceback.format_exc()}")
        # Try to wait a bit and continue - might still be able to take a screenshot
        try:
            await page.wait_for_timeout(2000)
            # Check if page is actually loaded despite error
            current_url = page.url
            logger.info(f"Current page URL after navigation error: {current_url}")
        except Exception as wait_error:
            logger.error(f"Failed to wait after navigation error: {wait_error}")
            raise Exception(f"Failed to navigate to {url}: {error_type}: {str(e)}") from e
    
    # After navigation, ensure Fast Refresh is still disabled
    try:
        await page.evaluate("""
            (function() {
                // Disable Next.js Fast Refresh
                if (window.__NEXT_DATA__) {
                    window.__NEXT_DATA__.dev = false;
                }
                // Disable HMR (Hot Module Replacement)
                if (window.__NEXT_HOT_RELOAD__) {
                    window.__NEXT_HOT_RELOAD__ = false;
                }
                // Prevent any WebSocket connections that might trigger refresh
                window.__NEXT_DISABLE_FAST_REFRESH = true;
                
                // Disconnect any existing WebSocket connections
                if (window.__NEXT_HOT_RELOAD_SOCKET__) {
                    try {
                        window.__NEXT_HOT_RELOAD_SOCKET__.close();
                    } catch(e) {}
                }
            })();
        """)
        logger.info("✅ Ensured Fast Refresh is disabled after navigation")
    except Exception as e:
        logger.warning(f"⚠️ Could not ensure Fast Refresh is disabled after navigation: {e}")
    
    # Wait for specific selector if provided (this is more reliable than networkidle)
    if wait_selector:
        try:
            logger.info(f"Waiting for selector: {wait_selector} (timeout: {min(60000, timeout)}ms)")
            # Wait up to 60 seconds for the selector (increased from 30)
            # For tables, wait for table to have actual rows (tbody tr or tr elements)
            if wait_selector == 'table':
                # Wait for table to exist AND have content
                await page.wait_for_function(
                    """
                    () => {
                        const tables = document.querySelectorAll('table');
                        if (tables.length === 0) return false;
                        // Check that at least one table has rows with content
                        for (const table of tables) {
                            const rows = table.querySelectorAll('tbody tr, tr');
                            // Need at least 2 rows (header + data row)
                            if (rows.length >= 2) {
                                // Check that rows have text content
                                let hasContent = false;
                                for (const row of rows) {
                                    if (row.textContent && row.textContent.trim().length > 0) {
                                        hasContent = true;
                                        break;
                                    }
                                }
                                if (hasContent) return true;
                            }
                        }
                        return false;
                    }
                    """,
                    timeout=min(60000, timeout)
                )
                logger.info(f"✅ Table found with content")
            else:
                # For other selectors, use standard wait
                await page.wait_for_selector(wait_selector, timeout=min(60000, timeout), state='visible')
                logger.info(f"✅ Selector {wait_selector} found and visible")
            
            # Additional wait to ensure content is fully rendered
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"⚠️ Selector {wait_selector} not found after timeout: {e}")
            # Continue anyway - might still be able to take a screenshot
            # But log this as a warning since it might indicate a problem
            # Wait a bit more anyway
            await page.wait_for_timeout(3000)
    
    # Wait for React to finish rendering and charts to load
    # Wait for any animations to settle
    await page.wait_for_timeout(3000)  # Increased from 2000 to 3000
    
    # Wait for charts to fully render with data AND text labels (Recharts components)
    # Check that SVG elements have actual content including text labels
    try:
        await page.wait_for_function(
            """
            () => {
                // Check for charts with data AND text labels
                const chartSvgs = document.querySelectorAll('[data-slot="chart"] svg');
                if (chartSvgs.length > 0) {
                    let chartsWithDataAndLabels = 0;
                    // Check if SVG has actual content (paths, circles, etc.) AND text labels
                    for (const svg of chartSvgs) {
                        const paths = svg.querySelectorAll('path, circle, rect, line');
                        const textElements = svg.querySelectorAll('text');
                        // Check that we have both visual elements AND text labels
                        if (paths.length > 0 && textElements.length > 0) {
                            // Verify text elements have actual content (not empty)
                            let hasTextContent = false;
                            for (const text of textElements) {
                                if (text.textContent && text.textContent.trim().length > 0) {
                                    hasTextContent = true;
                                    break;
                                }
                            }
                            if (hasTextContent) {
                                chartsWithDataAndLabels++;
                            }
                        }
                    }
                    // If we have charts, wait until at least some have both data and labels
                    if (chartSvgs.length > 0 && chartsWithDataAndLabels > 0) {
                        return true;
                    }
                }
                // Also check for tables
                const tables = document.querySelectorAll('table');
                if (tables.length > 0) {
                    // Check that tables have content (not just headers)
                    for (const table of tables) {
                        const rows = table.querySelectorAll('tbody tr, tr');
                        if (rows.length > 0) {
                            return true;
                        }
                    }
                }
                // If no charts or tables, return true anyway (might be a simple page)
                return true;
            }
            """,
            timeout=15000  # Reduced timeout to 15 seconds (from 20)
        )
        logger.info("✅ Charts or tables with data and labels detected")
    except Exception as e:
        logger.warning(f"⚠️ Charts/tables check timed out or failed: {e}")
        # Wait longer for charts and labels to render
        await page.wait_for_timeout(5000)
    
    # Additional wait for chart animations and text rendering to complete
    await page.wait_for_timeout(3000)
    
    # Force a reflow to ensure all text is rendered
    # Use page.wait_for_function instead of page.evaluate with Promise to avoid syntax issues
    await page.evaluate("""
        () => {
            // Force a reflow to ensure all text is rendered
            document.body.offsetHeight;
            // Force a second reflow
            void document.body.offsetHeight;
        }
    """)
    await page.wait_for_timeout(100)  # Wait for any pending animations
    
    # Collapse sidebar menu by directly manipulating the DOM
    # SidebarLayout uses useState, so we need to directly set the aside width
    await page.evaluate("""
        (function() {
            // Find sidebar element
            const sidebar = document.querySelector('aside');
            if (sidebar) {
                // Check if sidebar is expanded (w-64 means expanded, w-16 means collapsed)
                const isExpanded = sidebar.className.includes('w-64');
                if (isExpanded) {
                    // Replace w-64 with w-16 to collapse
                    sidebar.className = sidebar.className.replace('w-64', 'w-16');
                    // Also update any transition classes if needed
                    sidebar.style.width = '4rem'; // 64px = 4rem = w-16
                }
            }
            
            // Also try clicking the toggle button if it exists
            const sidebarToggle = document.querySelector('button[aria-label="Toggle sidebar"], button[aria-label*="sidebar" i]');
            if (sidebarToggle) {
                sidebarToggle.click();
            }
        })();
    """)
    
    # Wait for sidebar to collapse
    await page.wait_for_timeout(500)
    
    # Remove excessive spacing but don't modify table width
    # Table will be captured at its natural size and scaled to fixed size in PDF
    await page.evaluate("""
        (function() {
            // Find the table container div
            const container = document.querySelector('div.space-y-8');
            if (!container) return;
            
            // Only remove excessive margins/padding from container
            container.style.margin = '0';
            container.style.padding = '0';
            
            // Remove excessive margins from card but keep original padding
            const card = container.querySelector('div.bg-white.rounded-lg.shadow');
            if (card) {
                card.style.margin = '0';
            }
            
            // DON'T modify tables - capture them at their natural size
            // They will be scaled to fixed size (1200x900px) in PDF
            
            // Only remove excessive spacing from table wrapper
            const tableWrapper = container.querySelector('.bg-gray-50');
            if (tableWrapper) {
                tableWrapper.style.margin = '0';
            }
            
            // Only remove excessive spacing from headings
            const headings = container.querySelectorAll('h1, h2, h3');
            headings.forEach(heading => {
                heading.style.marginTop = '0';
            });
        })();
    """)
    
    # Wait longer after CSS optimization to ensure all styles are applied
    await page.wait_for_timeout(2000)  # Increased from 1000 to ensure styles are fully applied
    
    # Find the specific div containing the Summary Metrics table
    # The div structure is: div.space-y-8 > div.bg-white.rounded-lg.shadow.p-6 > div.space-y-4 > div.bg-gray-50 (table wrapper)
    # We want to capture the entire content including the card container
    logger.info("Finding Summary Metrics container div...")
    try:
        # Wait for the table to be visible first
        await page.wait_for_selector('table', timeout=10000, state='visible')
        logger.info("✅ Table found")
        
        # Find the parent container div with class "space-y-8" that contains the Summary Metrics card
        # This is the outermost container that includes the card with the table
        table_container = await page.query_selector('div.space-y-8')
        if not table_container:
            # Fallback: try to find the card container directly
            logger.warning("⚠️ Could not find div.space-y-8, trying card container...")
            table_container = await page.query_selector('div.bg-white.rounded-lg.shadow')
            if not table_container:
                logger.warning("⚠️ Could not find card container, falling back to full page screenshot")
                table_container = None
            else:
                logger.info("✅ Found card container")
        else:
            logger.info("✅ Found space-y-8 container div")
    except Exception as e:
        logger.warning(f"⚠️ Could not find table container div: {e}. Falling back to full page screenshot")
        table_container = None
    
    # Take screenshot of specific element or full page
    logger.info("Taking screenshot...")
    try:
        if table_container:
            logger.debug(f"Taking screenshot of table container element")
            screenshot = await table_container.screenshot(
                type='png'
            )
        else:
            logger.debug(f"Falling back to full page screenshot")
            screenshot = await page.screenshot(
                full_page=True,
                type='png',
                clip=None  # Full page
            )
        
        logger.info(f"✅ Screenshot taken successfully: {len(screenshot) if screenshot else 0} bytes")
        
        # CRITICAL: Validate screenshot before returning
        if screenshot is None:
            raise Exception(f"Screenshot returned None for {url}")
        
        if not isinstance(screenshot, bytes):
            raise Exception(f"Screenshot returned non-bytes type ({type(screenshot)}) for {url}")
        
        if len(screenshot) == 0:
            raise Exception(f"Empty screenshot returned for {url} (length: 0)")
        
        # Additional validation: PNG files should start with PNG signature
        if len(screenshot) >= 8 and screenshot[:8] != b'\x89PNG\r\n\x1a\n':
            logger.warning(f"⚠️ Screenshot for {url} doesn't have PNG signature (first 8 bytes: {screenshot[:8]})")
            # Don't fail here - might still be valid
        
        logger.info(f"✅ Screenshot captured: {len(screenshot)} bytes, format: PNG")
        
        # Enhanced validation logging
        if len(screenshot) < 1000:
            logger.warning(f"⚠️ Screenshot size is very small ({len(screenshot)} bytes) for {url}")
        elif len(screenshot) > 10_000_000:
            logger.warning(f"⚠️ Screenshot size is very large ({len(screenshot)} bytes) for {url}")
        else:
            logger.debug(f"Screenshot size is normal: {len(screenshot)} bytes")
        
        return screenshot
    except Exception as e:
        logger.error(f"❌ Error taking screenshot for {url}: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to capture screenshot for {url}: {str(e)}") from e


async def check_frontend_available(frontend_url: str) -> bool:
    """Check if frontend server is available."""
    if aiohttp is None:
        logger.warning("aiohttp not available, skipping frontend check")
        return True  # Continue anyway
    
    # Try multiple times with short delays (frontend might be starting up)
    for attempt in range(5):  # Increased attempts
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{frontend_url}/", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.info(f"✅ Frontend server is available at {frontend_url}")
                        return True
                    else:
                        logger.warning(f"Frontend server returned status {response.status} on attempt {attempt + 1}")
        except asyncio.TimeoutError:
            logger.warning(f"Frontend server check timeout on attempt {attempt + 1}")
        except Exception as e:
            logger.warning(f"Frontend server check failed on attempt {attempt + 1}: {e}")
        
        if attempt < 4:
            await asyncio.sleep(2)  # Wait 2 seconds before retry
    
    logger.error(f"❌ Frontend server is not available at {frontend_url} after 5 attempts")
    return False


async def build_weekly_reports_pdf_from_screenshots(
    base_week: str,
    frontend_url: str,
    config: Config,
    pages: List[Dict[str, Any]],
    progress_callback: Optional[Callable[[Dict[str, Any]], Union[None, Awaitable[None]]]] = None
) -> Path:
    """Build PDF from screenshots of web pages.
    
    Args:
        base_week: The base week to generate PDF for (e.g., "2025-44")
        frontend_url: Base URL of the frontend (e.g., "http://localhost:3000")
        config: Config object
        pages: List of page configs, each with:
            - path: URL path (e.g., "/summary")
            - title: Page title for PDF
            - wait_selector: CSS selector to wait for (optional)
            - skip: Whether to skip this page (optional)
    
    Returns:
        Path to generated PDF
    """
    logger.info(f"Building PDF from screenshots for week {base_week}")
    logger.info(f"Frontend URL: {frontend_url}")
    
    # Check if frontend is available
    logger.info("Checking if frontend server is available...")
    frontend_available = await check_frontend_available(frontend_url)
    if not frontend_available:
        raise Exception(
            f"Frontend server is not available at {frontend_url}. "
            f"Please make sure the frontend server is running. "
            f"Start it with: cd frontend && npm run dev"
        )
    logger.info("✅ Frontend server is available")
    
    output_path = config.reports_path / f"weekly_reports_{base_week}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter out skipped pages
    pages_to_capture = [p for p in pages if not p.get('skip', False)]
    
    if not pages_to_capture:
        raise Exception("No pages to capture. Please provide at least one page configuration.")
    
    logger.info(f"Will capture {len(pages_to_capture)} pages: {[p.get('title', p.get('path')) for p in pages_to_capture]}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--force-device-scale-factor=3',  # Match device_scale_factor in context
                '--high-dpi-support=1',  # Enable high DPI support
            ]
        )
        context = await browser.new_context(
            viewport={'width': 5120, 'height': 2880},  # 5K resolution for maximum sharpness
            device_scale_factor=3,  # High DPI for sharp text
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            ignore_https_errors=True,  # Ignore SSL errors if any
            java_script_enabled=True,
        )
        page = await context.new_page()
        
        screenshots = []
        failed_pages = []
        
        try:
            # Report progress: initializing browser
            if progress_callback:
                try:
                    result = progress_callback({
                        'step': 'initializing',
                        'stepNumber': 1,
                        'totalSteps': len(pages_to_capture) + 2,
                        'message': 'Initializing browser...',
                        'currentPage': None,
                        'percentage': 1
                    })
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            # Set localStorage BEFORE navigating to any pages
            # This ensures all pages use the correct week
            logger.info("Setting week in localStorage...")
            try:
                # Navigate to a page first to initialize localStorage
                await page.goto(f"{frontend_url}/settings", wait_until='domcontentloaded', timeout=30000)
                logger.info("✅ Navigated to settings page")
            except Exception as e:
                logger.warning(f"⚠️ Could not navigate to settings page: {e}. Trying to set localStorage anyway...")
            
            # Set localStorage and wait for it to be applied
            try:
                # Use a proper way to set localStorage with the base_week value
                await page.evaluate(f"""
                    (function() {{
                        localStorage.setItem('selected_week', '{base_week}');
                        localStorage.setItem('selectedWeek', '{base_week}');
                        // Dispatch storage event to notify context
                        window.dispatchEvent(new Event('storage'));
                        console.log('✅ Set localStorage selectedWeek to {base_week}');
                    }})();
                """)
                logger.info(f"✅ Set localStorage selectedWeek to {base_week}")
                
                # Verify it was set
                stored_value = await page.evaluate("localStorage.getItem('selected_week') || localStorage.getItem('selectedWeek')")
                if stored_value != base_week:
                    logger.warning(f"⚠️ localStorage value mismatch: expected {base_week}, got {stored_value}")
                else:
                    logger.info(f"✅ Verified localStorage value: {stored_value}")
            except Exception as e:
                logger.error(f"❌ Could not set localStorage: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Don't fail here - might still work
            
            # Wait longer for localStorage to be set and context to update
            await page.wait_for_timeout(2000)  # Wait for React to read localStorage
            
            # Wait for data to be loaded by checking if periods exist in context
            # This ensures React has time to read localStorage and load data
            logger.info("Waiting for data to load...")
            try:
                await page.wait_for_function(
                    """
                    () => {
                        // Check if data is loaded by looking for periods or metrics in the page
                        // Look for elements that indicate data is loaded
                        const hasData = 
                            document.querySelector('[data-periods]') !== null ||
                            document.querySelector('table') !== null ||
                            document.querySelector('[data-slot="chart"]') !== null ||
                            document.body.textContent.includes('Summary') ||
                            document.body.textContent.includes('Top Markets');
                        
                        // Also check if we're past the loading state
                        const isLoading = 
                            document.body.textContent.includes('Loading') ||
                            document.body.textContent.includes('Initializing') ||
                            document.querySelector('[class*="spinner"]') !== null ||
                            document.querySelector('[class*="skeleton"]') !== null;
                        
                        return hasData && !isLoading;
                    }
                    """,
                    timeout=30000  # Reduced to 30 seconds for faster initial check
                )
                logger.info("✅ Data appears to be loaded")
            except Exception as e:
                logger.warning(f"⚠️ Data loading check timed out: {e}. Continuing anyway...")
                # Wait a bit more as fallback
                await page.wait_for_timeout(5000)
                logger.info("Waited additional 5 seconds as fallback")
            
            # Report progress: ready to capture
            if progress_callback:
                try:
                    result = progress_callback({
                        'step': 'ready',
                        'stepNumber': 1,
                        'totalSteps': len(pages_to_capture) + 2,
                        'message': 'Ready to capture screenshots...',
                        'currentPage': None,
                        'percentage': 2
                    })
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            total_pages = len(pages_to_capture)
            
            logger.info(f"🚀 Starting screenshot capture loop for {total_pages} pages")
            logger.info(f"   Screenshots list initialized: {type(screenshots)}, length: {len(screenshots)}")
            
            # Navigate to each page and take screenshot
            for i, page_config in enumerate(pages_to_capture):
                page_path = page_config['path']
                page_title = page_config.get('title', page_path)
                wait_selector = page_config.get('wait_selector')
                
                # Calculate progress - include combining step at the end
                # Total steps = pages + combining + complete = total_pages + 2
                # Progress is based on current page out of total steps
                total_steps = total_pages + 2
                progress_pct = int(((i + 1) / total_steps) * 100)
                
                # Report progress BEFORE capturing (so user knows what's about to happen)
                if progress_callback:
                    try:
                        result = progress_callback({
                            'step': 'capturing',
                            'stepNumber': i + 1,
                            'totalSteps': total_steps,
                            'message': f'Capturing screenshot: {page_title}',
                            'currentPage': page_title,
                            'percentage': progress_pct
                        })
                        # If callback is async, await it
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")
                
                logger.info(f"Capturing screenshot {i+1}/{total_pages}: {page_title}")
                
                try:
                    # Don't add week query parameter if we've already set it in localStorage
                    # The frontend should use localStorage value
                    url = f"{frontend_url}{page_path}"
                    logger.info(f"📸 Capturing screenshot {i+1}/{total_pages}: {page_title}")
                    logger.info(f"   URL: {url}")
                    logger.info(f"   Wait selector: {wait_selector}")
                    logger.info(f"   Base week (from localStorage): {base_week}")
                    logger.info(f"   Current screenshots count: {len(screenshots)}")
                    
                    # Use retry logic for screenshot capture with shorter timeout
                    # Wrap in asyncio.wait_for to ensure we don't hang forever
                    try:
                        screenshot_bytes = await asyncio.wait_for(
                            capture_page_screenshot_with_retry(
                                page, 
                                url, 
                                wait_selector=wait_selector,
                                timeout=90000,  # Increased to 90 seconds for data loading
                                max_retries=2  # Retry up to 2 times
                            ),
                            timeout=300.0  # Total timeout: 5 minutes per page (90s * 3 attempts max)
                        )
                        logger.info(f"   ✅ Screenshot bytes received: {len(screenshot_bytes) if screenshot_bytes else 0} bytes")
                    except asyncio.TimeoutError:
                        error_msg = f"Timeout after 5 minutes while capturing {page_title}"
                        logger.error(f"❌ {error_msg}")
                        failed_pages.append(f"{page_title} (timeout)")
                        logger.error(f"   Screenshots list length is now: {len(screenshots)}")
                        screenshot_bytes = None  # Set to None so validation below handles it
                        continue  # Skip this page, continue with next
                    except Exception as capture_error:
                        error_type = type(capture_error).__name__
                        error_msg = f"Failed to capture {page_title}: {error_type}: {str(capture_error)}"
                        logger.error(f"❌ {error_msg}")
                        logger.error(f"   Full error: {capture_error}")
                        import traceback
                        logger.error(f"   Traceback: {traceback.format_exc()}")
                        failed_pages.append(f"{page_title} ({error_type}: {str(capture_error)[:100]}...)")
                        screenshot_bytes = None
                        continue  # Skip this page, continue with next
                    
                    # CRITICAL: Check if screenshot_bytes is None or empty BEFORE appending
                    if screenshot_bytes is None:
                        error_msg = f"capture_page_screenshot returned None for {page_title}"
                        logger.error(f"❌ {error_msg}")
                        failed_pages.append(f"{page_title} (None return)")
                        logger.error(f"   Screenshots list length is now: {len(screenshots)}")
                        continue  # Skip this page, continue with next
                    
                    if not isinstance(screenshot_bytes, bytes):
                        error_msg = f"capture_page_screenshot returned non-bytes type ({type(screenshot_bytes)}) for {page_title}"
                        logger.error(f"❌ {error_msg}")
                        failed_pages.append(f"{page_title} (wrong type)")
                        logger.error(f"   Screenshots list length is now: {len(screenshots)}")
                        continue  # Skip this page, continue with next
                    
                    if len(screenshot_bytes) == 0:
                        error_msg = f"capture_page_screenshot returned empty bytes for {page_title}"
                        logger.error(f"❌ {error_msg}")
                        failed_pages.append(f"{page_title} (empty bytes)")
                        logger.error(f"   Screenshots list length is now: {len(screenshots)}")
                        continue  # Skip this page, continue with next
                    
                    # Defensive check: Ensure screenshots list is still valid
                    if screenshots is None:
                        logger.error(f"❌ CRITICAL: Screenshots list is None before appending {page_title}")
                        failed_pages.append(f"{page_title} (screenshots list is None)")
                        continue
                    
                    if not isinstance(screenshots, list):
                        logger.error(f"❌ CRITICAL: Screenshots list is not a list (type: {type(screenshots)}) before appending {page_title}")
                        failed_pages.append(f"{page_title} (screenshots list corrupted)")
                        continue
                    
                    # Only append if we have valid screenshot data
                    screenshots_before = len(screenshots)
                    try:
                        screenshots.append({
                            'title': page_title,
                            'bytes': screenshot_bytes
                        })
                        screenshots_after = len(screenshots)
                        
                        if screenshots_after != screenshots_before + 1:
                            logger.error(f"❌ CRITICAL: Screenshot append failed! Before: {screenshots_before}, After: {screenshots_after}")
                            failed_pages.append(f"{page_title} (append failed)")
                            continue
                        
                        logger.info(f"✅ Successfully captured {page_title} ({len(screenshot_bytes)} bytes). Total screenshots: {len(screenshots)}")
                    except Exception as append_error:
                        logger.error(f"❌ CRITICAL: Exception during append: {type(append_error).__name__}: {str(append_error)}")
                        failed_pages.append(f"{page_title} (append exception: {str(append_error)[:50]})")
                        continue
                    
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = f"Failed to capture {page_title}: {error_type}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    failed_pages.append(f"{page_title} ({error_type}: {str(e)[:50]}...)")
                    # Continue with next page even if one fails
                    continue
            
            # After loop completes, check if we have any screenshots
            logger.info(f"🔄 Screenshot loop completed. Screenshots: {len(screenshots)}, Failed: {len(failed_pages)}")
            
            # If no screenshots were captured at all, raise exception immediately
            if len(screenshots) == 0:
                if len(failed_pages) == total_pages:
                    error_msg = f"CRITICAL: All {total_pages} screenshot attempts failed. "
                    error_msg += f"Failed pages: {', '.join(failed_pages[:10])}..."  # Limit to first 10 for brevity
                    error_msg += f" Frontend URL: {frontend_url}. "
                    error_msg += "Check backend logs for detailed error messages."
                else:
                    error_msg = f"CRITICAL: No screenshots captured despite {total_pages - len(failed_pages)} successful attempts. "
                    error_msg += f"Failed pages: {', '.join(failed_pages) if failed_pages else 'none'}. "
                    error_msg += f"Frontend URL: {frontend_url}. "
                    error_msg += "Check backend logs for detailed error messages."
                logger.error(error_msg)
                logger.error(f"   Screenshots list state: type={type(screenshots)}, length={len(screenshots) if screenshots else 'None'}")
                raise Exception(error_msg)
            
            # Log summary of captured screenshots BEFORE checking if empty
            logger.info(f"Completed screenshot capture loop. Captured {len(screenshots)}/{total_pages} screenshots")
            logger.info(f"Screenshots list type: {type(screenshots)}, length: {len(screenshots) if screenshots else 'None'}")
            if failed_pages:
                logger.warning(f"Failed to capture {len(failed_pages)} pages: {', '.join(failed_pages)}")
            
            # CRITICAL: Only proceed with PDF building if we have screenshots
            # Check screenshots list is valid and not empty
            if screenshots is None:
                error_msg = f"Screenshots list is None after attempting {total_pages} pages. "
                error_msg += f"Failed pages: {', '.join(failed_pages) if failed_pages else 'none'}. "
                error_msg += f"Frontend URL: {frontend_url}. "
                error_msg += "Check backend logs for detailed error messages."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            if not isinstance(screenshots, list):
                error_msg = f"Screenshots list is not a list (type: {type(screenshots)}) after attempting {total_pages} pages. "
                error_msg += f"Failed pages: {', '.join(failed_pages) if failed_pages else 'none'}. "
                error_msg += f"Frontend URL: {frontend_url}. "
                error_msg += "Check backend logs for detailed error messages."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            if len(screenshots) == 0:
                error_msg = f"No screenshots captured after attempting {total_pages} pages. "
                error_msg += f"Failed pages: {', '.join(failed_pages) if failed_pages else 'none (all screenshots returned None/empty)'}. "
                error_msg += f"Frontend URL: {frontend_url}. "
                error_msg += "Check backend logs for detailed error messages."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"✅ Successfully captured {len(screenshots)} screenshots, proceeding with PDF generation")
            
            # Report progress: combining screenshots into PDF (ONLY if we have screenshots)
            total_steps = total_pages + 2
            if progress_callback and screenshots and len(screenshots) > 0:
                try:
                    result = progress_callback({
                        'step': 'combining',
                        'stepNumber': total_pages + 1,
                        'totalSteps': total_steps,
                        'message': 'Combining screenshots into PDF...',
                        'currentPage': None,
                        'percentage': int((total_pages / total_steps) * 100)
                    })
                    # If callback is async, await it
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            # Report progress: building PDF document (ONLY if we have screenshots)
            if progress_callback and screenshots and len(screenshots) > 0:
                try:
                    result = progress_callback({
                        'step': 'building',
                        'stepNumber': total_pages + 1,
                        'totalSteps': total_steps,
                        'message': 'Building PDF document...',
                        'currentPage': None,
                        'percentage': int(((total_pages + 1) / total_steps) * 100)
                    })
                    # If callback is async, await it
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            # Combine screenshots into PDF (INSIDE try block, BEFORE finally)
            logger.info(f"Starting PDF building. Screenshots list length: {len(screenshots)}")
            
            # Combine screenshots into PDF
            logger.info(f"Combining {len(screenshots)} screenshots into PDF...")
            
            # Use fixed image size approach:
            # - Target image size: 1200x900 px
            # - PDF page size: 1300x1000 px (1200+50+50 x 900+50+50)
            # - Margins: 50px (50 points) on all sides
            
            DPI = 300  # High DPI for maximum sharpness
            POINTS_PER_PIXEL = 72.0 / DPI
            
            # Fixed target image dimensions in pixels
            TARGET_IMAGE_WIDTH_PX = 1200
            TARGET_IMAGE_HEIGHT_PX = 900
            
            # Fixed margins in pixels (convert to points)
            MARGIN_PX = 50
            margin_points = MARGIN_PX * POINTS_PER_PIXEL
            
            # Calculate PDF page size based on target image size + margins
            target_width_pts = TARGET_IMAGE_WIDTH_PX * POINTS_PER_PIXEL
            target_height_pts = TARGET_IMAGE_HEIGHT_PX * POINTS_PER_PIXEL
            
            page_width = target_width_pts + 2 * margin_points
            page_height = target_height_pts + 2 * margin_points
            
            logger.info(f"Creating PDF with fixed size approach:")
            logger.info(f"  Target image size: {TARGET_IMAGE_WIDTH_PX} x {TARGET_IMAGE_HEIGHT_PX} px")
            logger.info(f"  PDF page size: {page_width:.2f} x {page_height:.2f} points")
            logger.info(f"  Margins: {MARGIN_PX} px ({margin_points:.2f} points) on all sides")
            
            # Create document with calculated page size
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=(page_width, page_height),
                rightMargin=margin_points,
                leftMargin=margin_points,
                topMargin=margin_points,
                bottomMargin=margin_points
            )
            
            # Available frame size equals target image size
            available_width = target_width_pts
            available_height = target_height_pts
            
            story = []
            
            # Add screenshot directly (no cover page)
            logger.info(f"Adding {len(screenshots)} screenshots to PDF...")
            for i, screenshot_data in enumerate(screenshots):
                if i > 0:
                    story.append(PageBreak())
                
                # Validate screenshot_data structure
                if not isinstance(screenshot_data, dict):
                    logger.error(f"Screenshot {i} is not a dict: {type(screenshot_data)}")
                    continue
                
                if 'bytes' not in screenshot_data:
                    logger.error(f"Screenshot {i} missing 'bytes' key. Keys: {screenshot_data.keys()}")
                    continue
                
                screenshot_bytes = screenshot_data['bytes']
                if not isinstance(screenshot_bytes, bytes):
                    logger.error(f"Screenshot {i} bytes is not bytes type: {type(screenshot_bytes)}")
                    continue
                
                if len(screenshot_bytes) == 0:
                    logger.error(f"Screenshot {i} has empty bytes")
                    continue
                
                # Convert bytes to PIL Image
                try:
                    img = Image.open(BytesIO(screenshot_bytes))
                except Exception as e:
                    logger.error(f"Failed to open screenshot {i} as image: {e}")
                    continue
                
                # Get image dimensions in pixels (PIL Image.size returns pixels)
                img_width_px, img_height_px = img.size
                logger.info(f"Screenshot {i} ({screenshot_data.get('title', 'Unknown')}): {img_width_px} x {img_height_px} pixels")
                
                # Scale image to exact target size (1200x900 px)
                # This will stretch/squash the image to fit exactly if aspect ratio doesn't match
                
                # Target dimensions in points (use same constants as defined above)
                target_width_pts = TARGET_IMAGE_WIDTH_PX * POINTS_PER_PIXEL
                target_height_pts = TARGET_IMAGE_HEIGHT_PX * POINTS_PER_PIXEL
                
                logger.debug(f"Image size: {img_width_px} x {img_height_px} pixels")
                logger.debug(f"Target size: {TARGET_IMAGE_WIDTH_PX} x {TARGET_IMAGE_HEIGHT_PX} px = {target_width_pts:.2f} x {target_height_pts:.2f} points")
                
                # Use exact target dimensions (no scaling, will stretch if needed)
                fit_width = target_width_pts
                fit_height = target_height_pts
                
                logger.debug(f"Final fit dimensions: {fit_width:.2f} x {fit_height:.2f} points (exact target size)")
                
                # Resize image to exact target size (this will stretch/squash if aspect ratio differs)
                # Calculate scale factors for width and height independently
                width_scale = TARGET_IMAGE_WIDTH_PX / img_width_px
                height_scale = TARGET_IMAGE_HEIGHT_PX / img_height_px
                
                logger.debug(f"Scaling factors: width={width_scale:.4f}, height={height_scale:.4f}")
                
                # Resize image to target size (may stretch/squash)
                new_width_px = TARGET_IMAGE_WIDTH_PX
                new_height_px = TARGET_IMAGE_HEIGHT_PX
                img_resized = img.resize((new_width_px, new_height_px), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {img_width_px}x{img_height_px} to {new_width_px}x{new_height_px} pixels")
                
                # Save to bytes with maximum quality
                img_bytes = BytesIO()
                img_resized.save(img_bytes, format='PNG', optimize=False, compress_level=1)
                img_bytes.seek(0)
                
                # Add to PDF using the exact target dimensions
                # fit_width and fit_height are already set to target_width_pts and target_height_pts
                # which match available_width and available_height exactly
                pdf_img = RLImage(img_bytes, width=fit_width, height=fit_height)
                story.append(pdf_img)
                logger.info(f"✅ Added screenshot {i} to PDF: {fit_width:.2f} x {fit_height:.2f} points (exact target size)")
            
            # Build PDF document
            logger.info(f"Building PDF document with {len(story)} elements...")
            doc.build(story)
            logger.info(f"✅ Successfully generated PDF: {output_path}")
            
            # Report completion
            total_steps = total_pages + 2
            
            # Create result object with file info
            # Ensure output_path exists and has a name attribute
            if output_path is None:
                raise Exception("output_path is None - PDF generation failed before file was created")
            
            # Safely extract filename from output_path
            try:
                pdf_filename = output_path.name if hasattr(output_path, 'name') else str(output_path).split('/')[-1]
            except Exception as e:
                logger.error(f"Failed to extract filename from output_path: {e}")
                # Fallback: generate a filename from base_week
                pdf_filename = f"weekly_reports_{base_week}.pdf"
                logger.warning(f"Using fallback filename: {pdf_filename}")
            
            result_data = {
                'success': True,
                'file_path': str(output_path),
                'download_url': f"/api/download/{pdf_filename}",
            }
            
            if progress_callback:
                try:
                    logger.info(f"Sending completion callback with result: {result_data}")
                    callback_data = {
                        'step': 'complete',
                        'stepNumber': total_steps,
                        'totalSteps': total_steps,
                        'message': 'PDF generation complete!',
                        'currentPage': None,
                        'percentage': 100,
                        'result': result_data  # Include result in completion callback
                    }
                    result = progress_callback(callback_data)
                    # If callback is async, await it
                    if asyncio.iscoroutine(result):
                        await result
                    logger.info("Completion callback sent successfully")
                except Exception as e:
                    logger.error(f"Progress callback error during completion: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Re-raise to ensure error is caught by caller
                    raise
            
            return output_path
                
        finally:
            await browser.close()
            logger.info("Browser closed")


async def build_weekly_reports_pdf_from_screenshots_async(
    base_week: str,
    frontend_url: str,
    config: Config,
    pages: List[Dict[str, Any]],
    progress_callback: Optional[Callable[[Dict[str, Any]], Union[None, Awaitable[None]]]] = None
) -> Path:
    """Async wrapper for async screenshot PDF builder.
    
    This is the async version that can be called directly from async FastAPI endpoints.
    """
    return await build_weekly_reports_pdf_from_screenshots(
        base_week, frontend_url, config, pages, progress_callback
    )

