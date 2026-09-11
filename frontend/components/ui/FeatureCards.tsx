'use client';

export function FeatureCards() {
  return (
    <section className="features-section fade-in-delay-3" aria-label="Features">
      <div className="features-grid">
        <article className="feature-card" id="feature-tech">
          <div className="feature-icon-wrap" aria-hidden="true">🛠</div>
          <h3 className="feature-title">Tech Detection</h3>
          <p className="feature-desc">
            วิเคราะห์ Framework, CMS, Library และเทคโนโลยีที่เว็บไซต์ใช้งาน
          </p>
        </article>
        <article className="feature-card" id="feature-security">
          <div className="feature-icon-wrap" aria-hidden="true">🔒</div>
          <h3 className="feature-title">Security Audit</h3>
          <p className="feature-desc">
            ตรวจหาช่องโหว่และจุดอ่อนด้านความปลอดภัยของเว็บไซต์
          </p>
        </article>
        <article className="feature-card" id="feature-automated">
          <div className="feature-icon-wrap" aria-hidden="true">📊</div>
          <h3 className="feature-title">Automated Analysis</h3>
          <p className="feature-desc">
            ประเมินและสรุปรายงานตามมาตรฐานความปลอดภัยแบบอัตโนมัติ
          </p>
        </article>
      </div>
    </section>
  );
}
