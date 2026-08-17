async function scan(url) {
    if (!url) {
        process.stdout.write(JSON.stringify({ error: 'No URL provided' }));
        process.exitCode = 1;
        return;
    }

    let chrome;
    try {
        // Dynamic import — lighthouse is ESM-only
        const { default: lighthouse } = await import('lighthouse');
        const chromeLauncher = await import('chrome-launcher');

        chrome = await chromeLauncher.launch({
            chromeFlags: [
                '--headless',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        });

        const result = await lighthouse(url, {
            logLevel: 'error',
            output: 'json',
            port: chrome.port,
            onlyCategories: [
                'performance',
                'accessibility',
                'best-practices',
                'seo',
            ],
        });

        const lhr = result.lhr;

        // Extract category scores (0-1 → 0-100)
        const categories = {};
        for (const [key, cat] of Object.entries(lhr.categories)) {
            categories[key] = {
                title: cat.title,
                score: cat.score !== null ? Math.round(cat.score * 100) : null,
            };
        }

        // Extract failed audits (score < 1 and not informational/manual)
        const failedAudits = [];
        for (const [id, audit] of Object.entries(lhr.audits)) {
            if (
                audit.score !== null &&
                audit.score < 1 &&
                audit.scoreDisplayMode !== 'informative' &&
                audit.scoreDisplayMode !== 'manual' &&
                audit.scoreDisplayMode !== 'notApplicable'
            ) {
                failedAudits.push({
                    id,
                    title: audit.title,
                    description: audit.description,
                    score: Math.round(audit.score * 100),
                    displayValue: audit.displayValue || null,
                });
            }
        }

        // Sort by score ascending (worst first)
        failedAudits.sort((a, b) => a.score - b.score);

        const output = {
            url,
            timestamp: new Date().toISOString(),
            categories,
            failed_audits: failedAudits.slice(0, 30), // limit to top 30
            total_failed: failedAudits.length,
            lighthouse_version: lhr.lighthouseVersion,
            fetch_time: lhr.fetchTime,
        };

        process.stdout.write(JSON.stringify(output));
    } catch (error) {
        process.stdout.write(
            JSON.stringify({ error: error.message || String(error) })
        );
        process.exitCode = 1;
    } finally {
        if (chrome) {
            try {
                await chrome.kill();
            } catch (_) {
                // ignore cleanup errors
            }
        }
    }
}

const url = process.argv[2];
scan(url);
