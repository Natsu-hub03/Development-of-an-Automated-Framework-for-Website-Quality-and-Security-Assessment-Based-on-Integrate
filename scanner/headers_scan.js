const https = require('https');
const http = require('http');
const tls = require('tls');
const { URL } = require('url');

/**
 * headers_scan.js
 * Scans HTTP response headers, TLS info, HTTPS enforcement,
 * and cookie attributes for a given URL.
 * 
 * Output: JSON with all header/TLS check results.
 */

async function fetchHeaders(targetUrl) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(targetUrl);
        const isHttps = parsedUrl.protocol === 'https:';
        const mod = isHttps ? https : http;

        const req = mod.get(targetUrl, {
            timeout: 15000,
            headers: {
                'User-Agent': 'WebScan-HeaderScanner/1.0',
            },
            // Don't follow redirects automatically — we want to inspect them
            maxRedirects: 0,
        }, (res) => {
            // Collect TLS info if HTTPS
            let tlsInfo = null;
            if (isHttps && req.socket) {
                try {
                    const cipher = req.socket.getCipher?.();
                    const protocol = req.socket.getProtocol?.();
                    const cert = req.socket.getPeerCertificate?.();
                    tlsInfo = {
                        protocol: protocol || null,
                        cipher_name: cipher?.name || null,
                        cipher_version: cipher?.version || null,
                        cert_subject: cert?.subject?.CN || null,
                        cert_issuer: cert?.issuer?.CN || null,
                        cert_valid_from: cert?.valid_from || null,
                        cert_valid_to: cert?.valid_to || null,
                    };
                } catch (_) { /* ignore */ }
            }

            resolve({
                statusCode: res.statusCode,
                headers: res.headers,
                tlsInfo,
            });
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timed out'));
        });
    });
}

async function checkHttpsRedirect(targetUrl) {
    // If URL is already HTTPS, check if HTTP version redirects to HTTPS
    const parsedUrl = new URL(targetUrl);
    if (parsedUrl.protocol === 'https:') {
        const httpUrl = targetUrl.replace(/^https:/, 'http:');
        try {
            return await new Promise((resolve) => {
                const req = http.get(httpUrl, {
                    timeout: 10000,
                    headers: { 'User-Agent': 'WebScan-HeaderScanner/1.0' },
                }, (res) => {
                    const location = res.headers['location'] || '';
                    const redirectsToHttps = (res.statusCode >= 300 && res.statusCode < 400)
                        && location.startsWith('https');
                    resolve({
                        checked: true,
                        redirects_to_https: redirectsToHttps,
                        status_code: res.statusCode,
                        location: location || null,
                    });
                });
                req.on('error', () => resolve({ checked: true, redirects_to_https: false, error: 'HTTP request failed' }));
                req.on('timeout', () => {
                    req.destroy();
                    resolve({ checked: true, redirects_to_https: false, error: 'HTTP request timed out' });
                });
            });
        } catch {
            return { checked: false, redirects_to_https: false, error: 'Could not check HTTP redirect' };
        }
    }
    return { checked: false, redirects_to_https: false, note: 'URL is not HTTPS' };
}

async function getTlsDetails(hostname) {
    return new Promise((resolve) => {
        const socket = tls.connect({
            host: hostname,
            port: 443,
            timeout: 10000,
            servername: hostname,
        }, () => {
            const cipher = socket.getCipher();
            const protocol = socket.getProtocol();
            const cert = socket.getPeerCertificate();

            socket.destroy();
            resolve({
                protocol: protocol,
                cipher_name: cipher?.name || null,
                cipher_standard_name: cipher?.standardName || null,
                cipher_version: cipher?.version || null,
                cert_subject: cert?.subject?.CN || null,
                cert_issuer: cert?.issuer?.CN || null,
                cert_valid_from: cert?.valid_from || null,
                cert_valid_to: cert?.valid_to || null,
                cert_fingerprint: cert?.fingerprint256 || null,
            });
        });

        socket.on('error', (err) => {
            socket.destroy();
            resolve({ error: err.message });
        });
        socket.on('timeout', () => {
            socket.destroy();
            resolve({ error: 'TLS connection timed out' });
        });
    });
}

function parseSetCookieHeaders(headers) {
    const setCookieHeaders = headers['set-cookie'] || [];
    if (!Array.isArray(setCookieHeaders) || setCookieHeaders.length === 0) {
        return { has_cookies: false, cookies: [] };
    }

    const cookies = setCookieHeaders.map((raw) => {
        const parts = raw.split(';').map(p => p.trim());
        const nameValue = parts[0] || '';
        const name = nameValue.split('=')[0] || '';
        const flags = parts.slice(1).map(p => p.toLowerCase());

        return {
            name,
            secure: flags.some(f => f === 'secure'),
            httpOnly: flags.some(f => f === 'httponly'),
            sameSite: flags.find(f => f.startsWith('samesite'))?.split('=')[1]?.trim() || null,
            hasExpiry: flags.some(f => f.startsWith('expires') || f.startsWith('max-age')),
            raw: raw,
        };
    });

    return { has_cookies: true, cookies };
}

async function scan(url) {
    if (!url) {
        process.stdout.write(JSON.stringify({ error: 'No URL provided' }));
        process.exitCode = 1;
        return;
    }

    try {
        // Ensure URL starts with http/https
        let targetUrl = url;
        if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
            targetUrl = 'https://' + targetUrl;
        }

        const parsedUrl = new URL(targetUrl);
        const isHttps = parsedUrl.protocol === 'https:';

        // 1. Fetch response headers (use HTTPS URL if available)
        const httpsUrl = isHttps ? targetUrl : targetUrl.replace(/^http:/, 'https:');
        let headerResult;
        try {
            headerResult = await fetchHeaders(httpsUrl);
        } catch {
            // Fallback to original URL
            headerResult = await fetchHeaders(targetUrl);
        }

        // 2. Check HTTPS redirect (HTTP → HTTPS)
        const httpsRedirect = await checkHttpsRedirect(httpsUrl);

        // 3. Get detailed TLS info
        let tlsDetails = null;
        if (isHttps || httpsUrl.startsWith('https:')) {
            tlsDetails = await getTlsDetails(parsedUrl.hostname);
        }

        // 4. Parse cookies
        const cookieInfo = parseSetCookieHeaders(headerResult.headers);

        // 5. Build output
        const h = headerResult.headers;
        const output = {
            url: targetUrl,
            timestamp: new Date().toISOString(),
            status_code: headerResult.statusCode,
            is_https: isHttps,
            https_redirect: httpsRedirect,
            tls: tlsDetails,
            cookies: cookieInfo,
            // All security headers — raw values
            security_headers: {
                'content-security-policy': h['content-security-policy'] || null,
                'strict-transport-security': h['strict-transport-security'] || null,
                'x-frame-options': h['x-frame-options'] || null,
                'x-content-type-options': h['x-content-type-options'] || null,
                'referrer-policy': h['referrer-policy'] || null,
                'permissions-policy': h['permissions-policy'] || null,
                'cross-origin-opener-policy': h['cross-origin-opener-policy'] || null,
                'cross-origin-embedder-policy': h['cross-origin-embedder-policy'] || null,
                'cross-origin-resource-policy': h['cross-origin-resource-policy'] || null,
                'cache-control': h['cache-control'] || null,
                'x-permitted-cross-domain-policies': h['x-permitted-cross-domain-policies'] || null,
                'clear-site-data': h['clear-site-data'] || null,
                'x-xss-protection': h['x-xss-protection'] || null,
            },
            // Server info disclosure
            server_info: {
                server: h['server'] || null,
                'x-powered-by': h['x-powered-by'] || null,
            },
        };

        process.stdout.write(JSON.stringify(output));
    } catch (error) {
        process.stdout.write(
            JSON.stringify({ error: error.message || String(error) })
        );
        process.exitCode = 1;
    }
}

const url = process.argv[2];
scan(url);
