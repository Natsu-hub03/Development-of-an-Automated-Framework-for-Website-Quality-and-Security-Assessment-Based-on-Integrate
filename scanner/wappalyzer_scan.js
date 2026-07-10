const Wappalyzer = require('wappalyzer-rm');

async function scan(url) {
    const wappalyzer = new Wappalyzer();
    await wappalyzer.init();

    try {
        const site = await wappalyzer.open(url);
        const results = await site.analyze();
        console.log(JSON.stringify(results, null, 2));
    } catch (error) {
        console.error(error);
    } finally {
        await wappalyzer.destroy();
    }
}

const url = process.argv[2];
scan(url);