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
            headless: true,
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

        // Build impact summary from violations
        const impactSummary = { critical: 0, serious: 0, moderate: 0, minor: 0 };
        for (const v of results.violations) {
            const impact = v.impact || 'minor';
            impactSummary[impact] = (impactSummary[impact] || 0) + 1;
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
                sample_target: v.nodes[0]?.target ?? [],
            })),
            passes_count: results.passes.length,
            incomplete: results.incomplete.map((inc) => ({
                id: inc.id,
                impact: inc.impact,
                description: inc.description,
                help: inc.help,
                nodes_count: inc.nodes.length,
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
