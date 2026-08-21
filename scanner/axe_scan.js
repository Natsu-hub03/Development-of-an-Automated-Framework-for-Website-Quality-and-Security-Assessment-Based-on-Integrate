const puppeteer = require('puppeteer');
const { AxePuppeteer } = require('@axe-core/puppeteer');

async function scan(url) {
    if (!url) {
        process.stdout.write(JSON.stringify({ error: 'No URL provided' }));
        process.exitCode = 1;
        return;
    }

    let browser;
    try {
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        });

        const page = await browser.newPage();

        // Bypass CSP so axe-core can inject its script into the page
        await page.setBypassCSP(true);

        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000,
        });

        const results = await new AxePuppeteer(page).analyze();

        // Extract clean page-level metadata for rules that target html/document
        const pageTitle = await page.title();
        const titleTagHtml = await page.evaluate(() => {
            const el = document.querySelector('title');
            return el ? el.outerHTML : '';
        });
        const langAttr = await page.evaluate(() => {
            const htmlEl = document.querySelector('html');
            return htmlEl ? htmlEl.getAttribute('lang') || '' : '';
        });

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
