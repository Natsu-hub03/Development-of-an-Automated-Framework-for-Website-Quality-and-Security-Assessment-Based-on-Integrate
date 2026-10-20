const defaultChrome = process.platform === 'win32' ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' : undefined;
if (!process.env.CHROMIUM_BIN && defaultChrome) {
    process.env.CHROMIUM_BIN = defaultChrome;
}
if (!process.env.PUPPETEER_EXECUTABLE_PATH && defaultChrome) {
    process.env.PUPPETEER_EXECUTABLE_PATH = defaultChrome;
}

const Wappalyzer = require('wappalyzer-rm');

async function scan(url) {
    if (!url) {
        process.stdout.write(JSON.stringify({ error: 'No URL provided' }));
        process.exitCode = 1;
        return;
    }

    const wappalyzer = new Wappalyzer({
        browser: {
            executablePath: process.env.CHROMIUM_BIN || defaultChrome,
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-crash-reporter',
                '--disable-breakpad',
                '--no-zygote',
            ],
        },
    });

    try {
        await wappalyzer.init();
        const site = await wappalyzer.open(url);
        const results = await site.analyze();
        process.stdout.write(JSON.stringify(results));
    } catch (error) {
        // Write error as JSON to stdout so backend can parse it
        process.stdout.write(JSON.stringify({ error: error.message || String(error) }));
        process.exitCode = 1;
    } finally {
        try {
            await wappalyzer.destroy();
        } catch (_) {
            // ignore cleanup errors
        }
    }
}

const url = process.argv[2];
scan(url);