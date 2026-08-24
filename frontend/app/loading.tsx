export default function Loading() {
  return (
    <div className="page-wrapper" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        <span className="spinner" style={{ width: '32px', height: '32px', borderTopColor: 'var(--accent)' }} aria-hidden="true" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)' }}>
          LOADING...
        </span>
      </div>
    </div>
  );
}
