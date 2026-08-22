'use client';

export function HeroSection() {
  return (
    <section className="hero-section fade-in-delay-1" aria-labelledby="hero-heading">
      <div className="hero-eyebrow" aria-hidden="true">
        <span className="hero-eyebrow-dot" />
        AI-Assisted Security Assessment
      </div>
      <h1 className="hero-title" id="hero-heading">
        Web Standards{' '}
        <span className="hero-title-accent">Scanner</span>
        <span className="hero-cursor" aria-hidden="true" />
      </h1>
      <p className="hero-subtitle">
        วิเคราะห์เทคโนโลยีและมาตรฐานเว็บไซต์ของคุณอย่างรวดเร็ว ปลอดภัย และแม่นยำ
      </p>
    </section>
  );
}
