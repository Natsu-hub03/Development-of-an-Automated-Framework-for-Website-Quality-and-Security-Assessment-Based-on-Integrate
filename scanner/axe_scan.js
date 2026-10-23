const fs = require('fs');
const puppeteer = require('puppeteer');

let axeSource = '';
try {
    axeSource = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
} catch (_) {}

async function scan(url) {
    if (!url) {
        process.stdout.write(JSON.stringify({ error: 'No URL provided' }));
        process.exitCode = 1;
        return;
    }

    let browser;
    try {
        const defaultChrome = process.platform === 'win32' ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' : undefined;
        browser = await puppeteer.launch({
            headless: true,
            executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || defaultChrome,
            protocolTimeout: 120000,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-crash-reporter',
                '--disable-breakpad',
                '--no-zygote',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
                '--allow-running-insecure-content',
            ],
        });

        const page = await browser.newPage();

        // Bypass CSP so axe-core can inject its script into the page
        await page.setBypassCSP(true);
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'th,en-US;q=0.9,en;q=0.8',
        });

        async function attemptNavigation(targetUrl) {
            try {
                await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 8000 });
                const curr = page.url() || '';
                if (!curr.startsWith('chrome-error://') && curr !== 'about:blank') {
                    return { success: true, finalUrl: curr };
                }
            } catch (e) {
                return { success: false, error: e };
            }
            return { success: false, error: new Error('Blank page') };
        }

        let fallbackUrl = null;
        if (url.startsWith('http://')) {
            fallbackUrl = url.replace('http://', 'https://');
        } else if (url.startsWith('https://')) {
            fallbackUrl = url.replace('https://', 'http://');
        }

        let navResult = await attemptNavigation(url);
        if (!navResult.success && fallbackUrl) {
            const fbResult = await attemptNavigation(fallbackUrl);
            if (fbResult.success) {
                navResult = fbResult;
            }
        }

        let results;
        async function evalAxeDirect() {
            await page.evaluate(axeSource);
            return await page.evaluate(async () => await axe.run(document, { iframes: false }));
        }

        async function fetchCleanHtml(targetUrl) {
            const urlsToTry = [targetUrl];
            if (targetUrl.startsWith('http://')) {
                urlsToTry.push(targetUrl.replace('http://', 'https://'));
            } else if (targetUrl.startsWith('https://')) {
                urlsToTry.push(targetUrl.replace('https://', 'http://'));
            }
            for (const u of urlsToTry) {
                try {
                    const resp = await fetch(u, {
                        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' },
                        signal: AbortSignal.timeout(10000)
                    });
                    if (resp.ok || resp.status < 400) {
                        const html = await resp.text();
                        return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
                    }
                } catch (_) {}
            }
            throw new Error(`Failed to fetch clean HTML from ${targetUrl}`);
        }

        async function evalAxeCleanDom(targetUrl) {
            const cleanHtml = await fetchCleanHtml(targetUrl);
            await page.goto('about:blank');
            await page.setContent(cleanHtml, { waitUntil: 'domcontentloaded', timeout: 15000 });
            await page.evaluate(axeSource);
            return await page.evaluate(async () => await axe.run(document, { iframes: false }));
        }

        function withTimeout(promise, ms) {
            return Promise.race([
                promise,
                new Promise((_, reject) => setTimeout(() => reject(new Error('Evaluation timed out')), ms))
            ]);
        }

        const currentUrl = page.url() || '';
        if (!navResult.success || currentUrl.startsWith('chrome-error://') || currentUrl === 'about:blank') {
            try {
                results = await evalAxeCleanDom(fallbackUrl || url);
            } catch (cleanErr) {
                throw new Error(`Failed to navigate to ${url}: ${navResult.error ? navResult.error.message : 'Page unreachable'}`);
            }
        } else {
            await new Promise(r => setTimeout(r, 1500));
            try {
                results = await withTimeout(evalAxeDirect(), 8000);
            } catch (err) {
                try {
                    const targetU = page.url() && !page.url().startsWith('about:') ? page.url() : url;
                    results = await evalAxeCleanDom(targetU);
                } catch (fallbackErr) {
                    throw err;
                }
            }
        }

        // Extract clean page-level metadata for rules that target html/document
        let pageTitle = '';
        let titleTagHtml = '';
        let langAttr = '';
        try {
            pageTitle = await page.title();
            titleTagHtml = await page.evaluate(() => {
                const el = document.querySelector('title');
                return el ? el.outerHTML : '';
            });
            langAttr = await page.evaluate(() => {
                const htmlEl = document.querySelector('html');
                return htmlEl ? htmlEl.getAttribute('lang') || '' : '';
            });
        } catch (_) {}

        // Build impact summary from violations
        const impactSummary = { critical: 0, serious: 0, moderate: 0, minor: 0 };
        for (const v of results.violations) {
            const impact = v.impact || 'minor';
            impactSummary[impact] = (impactSummary[impact] || 0) + 1;
        }

        function cleanSnippet(html) {
            if (!html) return '';
            const t = html.trim();
            if (t.startsWith('<html') && t.includes('>')) return t.substring(0, t.indexOf('>') + 1);
            if (t.startsWith('<body') && t.includes('>')) return t.substring(0, t.indexOf('>') + 1);
            if (t.length > 240) return t.substring(0, 240) + '...';
            return t;
        }

        function sanitizeNode(ruleId, node) {
            let target = node.target ?? [];
            let html = cleanSnippet(node.html);

            if (ruleId === 'document-title') {
                target = ['head > title'];
                html = titleTagHtml || (pageTitle ? `<title>${pageTitle}</title>` : '<title></title>');
            } else if (ruleId === 'html-has-lang' || ruleId === 'html-lang-valid') {
                target = ['html'];
                html = langAttr ? `<html lang="${langAttr}">` : '<html>';
            }

            return {
                target,
                html,
                failureSummary: node.failureSummary ?? '',
            };
        }

        const output = {
            url,
            timestamp: new Date().toISOString(),
            violations: results.violations.map((v) => ({
                id: v.id,
                impact: v.impact,
                description: v.description,
                help: v.help,
                helpUrl: v.helpUrl,
                tags: v.tags,
                nodes_count: v.nodes.length,
                // Include first node's target for context
                sample_target: v.id === 'document-title' ? ['head > title'] : (v.nodes[0]?.target ?? []),
                // Full node evidence for dashboard display
                nodes: v.nodes.slice(0, 5).map((n) => sanitizeNode(v.id, n)),
            })),
            passes_count: results.passes.length,
            passes: results.passes.map((p) => ({
                id: p.id,
                impact: p.impact,
                description: p.description,
                help: p.help,
                helpUrl: p.helpUrl,
                tags: p.tags,
                nodes_count: p.nodes?.length ?? 0,
                nodes: (p.nodes || []).slice(0, 3).map((n) => sanitizeNode(p.id, n)),
            })),
            incomplete: results.incomplete.map((inc) => ({
                id: inc.id,
                impact: inc.impact,
                description: inc.description,
                help: inc.help,
                nodes_count: inc.nodes.length,
                nodes: inc.nodes.slice(0, 5).map((n) => sanitizeNode(inc.id, n)),
            })),
            inapplicable_count: results.inapplicable.length,
            impact_summary: impactSummary,
            total_violations: results.violations.length,
        };

        process.stdout.write(JSON.stringify(output));
    } catch (error) {
        process.stdout.write(
            JSON.stringify({ error: error.message || String(error) })
        );
        process.exitCode = 1;
    } finally {
        if (browser) {
            try {
                await browser.close();
            } catch (_) {
                // ignore cleanup errors
            }
        }
    }
}

const url = process.argv[2];
scan(url);
