'use client';
import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleScan = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('http://localhost:8000/scan/wappalyzer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({ error: 'Failed to connect to backend' });
    }
    setLoading(false);
  };

  return (
    <main style={{ padding: 40, fontFamily: 'sans-serif' }}>
      <h1>Web Standard Scanner</h1>
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com"
        style={{ padding: 8, width: 300, marginRight: 8 }}
      />
      <button onClick={handleScan} disabled={loading || !url} style={{ padding: 8 }}>
        {loading ? 'Scanning...' : 'Scan'}
      </button>

      {result && (
        <pre style={{ marginTop: 20, background: '#f4f4f4', padding: 16, overflow: 'auto' }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </main>
  );
}