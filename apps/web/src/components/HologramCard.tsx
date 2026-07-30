import React, { useRef, useCallback, useEffect } from 'react';

interface HologramCardProps {
  children: React.ReactNode;
  className?: string;
  /** Max tilt angle in degrees. Default 4 (subtle) */
  tilt?: number;
}

/**
 * A CSS-3D perspective card that:
 *  - Tilts toward the cursor on hover
 *  - Shows a radial holographic shimmer following the mouse
 *  - Resets smoothly on mouse-leave
 */
export function HologramCard({ children, className = '', tilt = 4 }: HologramCardProps) {
  const cardRef  = useRef<HTMLDivElement>(null);
  const rafRef   = useRef<number>(0);
  const targetRef = useRef({ rotX: 0, rotY: 0, mx: 50, my: 50 });
  const currentRef = useRef({ rotX: 0, rotY: 0, mx: 50, my: 50 });

  // Smooth lerp loop
  useEffect(() => {
    const loop = () => {
      const t = targetRef.current;
      const c = currentRef.current;
      const ease = 0.04;  // slower, smoother interpolation
      c.rotX += (t.rotX - c.rotX) * ease;
      c.rotY += (t.rotY - c.rotY) * ease;
      c.mx   += (t.mx   - c.mx)   * ease;
      c.my   += (t.my   - c.my)   * ease;

      if (cardRef.current) {
        cardRef.current.style.transform =
          `perspective(1100px) rotateX(${c.rotX}deg) rotateY(${c.rotY}deg)`;
        cardRef.current.style.setProperty('--mouse-x', `${c.mx}%`);
        cardRef.current.style.setProperty('--mouse-y', `${c.my}%`);
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;   // 0–1
    const y = (e.clientY - rect.top)  / rect.height;  // 0–1
    targetRef.current.rotX = (y - 0.5) * -tilt;
    targetRef.current.rotY = (x - 0.5) *  tilt;
    targetRef.current.mx   = x * 100;
    targetRef.current.my   = y * 100;
  }, [tilt]);

  const handleMouseLeave = useCallback(() => {
    targetRef.current.rotX = 0;
    targetRef.current.rotY = 0;
    targetRef.current.mx   = 50;
    targetRef.current.my   = 50;
  }, []);

  return (
    <div
      ref={cardRef}
      className={`hologram-card ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Corner decorations */}
      <div className="card-corner tl" />
      <div className="card-corner tr" />
      <div className="card-corner bl" />
      <div className="card-corner br" />

      {/* Content */}
      <div className="card-inner">{children}</div>
    </div>
  );
}
