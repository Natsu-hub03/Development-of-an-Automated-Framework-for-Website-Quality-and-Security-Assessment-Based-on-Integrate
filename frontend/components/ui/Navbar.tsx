'use client';
import Link from 'next/link';

export function Navbar() {
  return (
    <nav className="navbar fade-in" role="navigation" aria-label="Main navigation">
      <Link href="/" className="navbar-brand" id="nav-home-link">
        <div className="navbar-logo" aria-hidden="true">W</div>
        <span className="navbar-title">WebScan</span>
      </Link>
      <div className="navbar-right">
        <div className="navbar-status-dot" aria-hidden="true" />
        <span>ONLINE</span>
        <span className="navbar-badge">v1.0</span>
      </div>
    </nav>
  );
}
