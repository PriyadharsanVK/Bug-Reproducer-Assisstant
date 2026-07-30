import { useCallback, useEffect, useRef } from 'react';

/**
 * useSoundFX — All sounds generated programmatically via Web Audio API.
 * No external files, no libraries, no network requests.
 * Designed to match the cyberpunk/sci-fi aesthetic of the app.
 *
 * Browser autoplay policy fix:
 * The AudioContext is created lazily and an unlock listener is registered
 * on the first user gesture (click / keydown / touchstart) so that sounds
 * are reliably available even before the very first button press.
 */
export function useSoundFX() {
  const ctxRef    = useRef<AudioContext | null>(null);
  const unlockedRef = useRef(false);

  /** Create (or reuse) the AudioContext and ensure it is running. */
  const getCtx = useCallback((): AudioContext | null => {
    if (typeof window === 'undefined') return null;

    if (!ctxRef.current) {
      ctxRef.current = new (
        window.AudioContext || (window as any).webkitAudioContext
      )();
    }

    const ctx = ctxRef.current;

    // If still suspended, kick it — this is safe to call repeatedly
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {/* ignore */});
    }

    return ctx;
  }, []);

  /**
   * Register a one-time document-level unlock on first user gesture.
   * This creates the AudioContext early so subsequent playback never
   * gets blocked by the browser's autoplay policy.
   */
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const unlock = () => {
      if (unlockedRef.current) return;
      unlockedRef.current = true;

      if (!ctxRef.current) {
        ctxRef.current = new (
          window.AudioContext || (window as any).webkitAudioContext
        )();
      }
      ctxRef.current.resume().catch(() => {/* ignore */});

      // Remove listeners once unlocked
      document.removeEventListener('click',     unlock);
      document.removeEventListener('keydown',   unlock);
      document.removeEventListener('touchstart', unlock);
    };

    document.addEventListener('click',      unlock, { once: true });
    document.addEventListener('keydown',    unlock, { once: true });
    document.addEventListener('touchstart', unlock, { once: true, passive: true });

    return () => {
      document.removeEventListener('click',     unlock);
      document.removeEventListener('keydown',   unlock);
      document.removeEventListener('touchstart', unlock);
    };
  }, []);

  /* ── Shared node builder ─────────────────────────────── */
  const makeOsc = (
    ctx: AudioContext,
    type: OscillatorType,
    dest: AudioNode = ctx.destination,
  ): [OscillatorNode, GainNode] => {
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.connect(gain);
    gain.connect(dest);
    return [osc, gain];
  };

  /* ── CLICK — descending cyber-blip ──────────────────── */
  const playClick = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    const [osc, gain] = makeOsc(ctx, 'square');

    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(220, now + 0.08);
    gain.gain.setValueAtTime(0.18, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

    osc.start(now);
    osc.stop(now + 0.12);
  }, [getCtx]);

  /* ── SUBMIT — layered ascending launch tone ─────────── */
  const playSubmit = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;

    // Layer 1 — ascending sweep
    const [osc1, gain1] = makeOsc(ctx, 'sawtooth');
    osc1.frequency.setValueAtTime(110, now);
    osc1.frequency.exponentialRampToValueAtTime(880, now + 0.22);
    gain1.gain.setValueAtTime(0.0, now);
    gain1.gain.linearRampToValueAtTime(0.12, now + 0.04);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
    osc1.start(now);
    osc1.stop(now + 0.30);

    // Layer 2 — confirmation ding at peak
    const [osc2, gain2] = makeOsc(ctx, 'sine');
    osc2.frequency.setValueAtTime(1760, now + 0.20);
    gain2.gain.setValueAtTime(0.0, now + 0.20);
    gain2.gain.linearRampToValueAtTime(0.15, now + 0.24);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
    osc2.start(now + 0.20);
    osc2.stop(now + 0.58);
  }, [getCtx]);

  /* ── TAB — soft triangle tick ───────────────────────── */
  const playTab = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    const [osc, gain] = makeOsc(ctx, 'triangle');

    osc.frequency.setValueAtTime(1200, now);
    osc.frequency.exponentialRampToValueAtTime(600, now + 0.05);
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);

    osc.start(now);
    osc.stop(now + 0.08);
  }, [getCtx]);

  /* ── SUCCESS — ascending chord arpeggio ─────────────── */
  const playSuccess = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;

    [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
      const [osc, gain] = makeOsc(ctx, 'sine');
      const t = now + i * 0.07;
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.0, t);
      gain.gain.linearRampToValueAtTime(0.13, t + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
      osc.start(t);
      osc.stop(t + 0.38);
    });
  }, [getCtx]);

  /* ── HOVER — ultra-subtle high-freq shimmer ─────────── */
  const playHover = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    const [osc, gain] = makeOsc(ctx, 'sine');

    osc.frequency.setValueAtTime(3200, now);
    osc.frequency.exponentialRampToValueAtTime(4000, now + 0.03);
    gain.gain.setValueAtTime(0.04, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

    osc.start(now);
    osc.stop(now + 0.05);
  }, [getCtx]);

  /* ── COPY — double-blip confirm ─────────────────────── */
  const playCopy = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;

    [0, 0.09].forEach((offset) => {
      const [osc, gain] = makeOsc(ctx, 'sine');
      osc.frequency.setValueAtTime(1320, now + offset);
      osc.frequency.exponentialRampToValueAtTime(1760, now + offset + 0.06);
      gain.gain.setValueAtTime(0.12, now + offset);
      gain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.08);
      osc.start(now + offset);
      osc.stop(now + offset + 0.10);
    });
  }, [getCtx]);

  /* ── DOWNLOAD — descending sweep + soft thud ─────────── */
  const playDownload = useCallback(() => {
    const ctx = getCtx();
    if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;

    const [osc1, gain1] = makeOsc(ctx, 'sawtooth');
    osc1.frequency.setValueAtTime(660, now);
    osc1.frequency.exponentialRampToValueAtTime(110, now + 0.18);
    gain1.gain.setValueAtTime(0.14, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
    osc1.start(now);
    osc1.stop(now + 0.24);

    const [osc2, gain2] = makeOsc(ctx, 'sine');
    osc2.frequency.setValueAtTime(80, now + 0.16);
    gain2.gain.setValueAtTime(0.18, now + 0.16);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.32);
    osc2.start(now + 0.16);
    osc2.stop(now + 0.34);
  }, [getCtx]);

  return { playClick, playSubmit, playTab, playSuccess, playHover, playCopy, playDownload };
}
