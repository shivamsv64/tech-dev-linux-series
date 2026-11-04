import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Audio, Img, Sequence, continueRender, delayRender, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';

// ------------------------------------------------------------------ types (props come from make_props.py)
export type Word = {w: string; s: number; e: number};
type At = {at: number};
export type Beat = {type: string; from: number; to: number; [k: string]: any};
export type OpenerProps = {
  duration: number; words: Word[]; beats: Beat[]; show: string; badge: string; look: 'mission' | 'city';
  voice?: string; voiceAt?: number; music?: string; sfx?: {file: string; at: number; vol?: number}[];
};

// ------------------------------------------------------------------ palette & fonts
const C = {
  navy: '#0a0f1f', ink: '#16130f', paper: '#ece3cf', paper2: '#e2d6bb', kraft: '#b98f58', red: '#d7263d',
  cyan: '#38bdf8', amber: '#fbbf24', violet: '#a78bfa', green: '#34d399', white: '#f1f5f9', muted: '#94a3b8',
};
const ACC: Record<string, string> = {accent: C.cyan, warm: C.amber, purple: C.violet, ok: C.green, bad: C.red, red: C.red, cyan: C.cyan, amber: C.amber, violet: C.violet};
const col = (c?: string) => (c && (ACC[c] || c)) || C.white;
const FONTS: [string, string][] = [
  ['Anton', 'fonts/Anton-Regular.ttf'], ['Bebas', 'fonts/BebasNeue-Regular.ttf'], ['Marker', 'fonts/PermanentMarker-Regular.ttf'],
  ['Typewriter', 'fonts/SpecialElite-Regular.ttf'], ['Abril', 'fonts/AbrilFatface-Regular.ttf'], ['Fraktur', 'fonts/UnifrakturMaguntia-Book.ttf'],
  ['VT', 'fonts/VT323-Regular.ttf'], ['Caveat', 'fonts/Caveat.ttf'], ['Poppins', 'fonts/Poppins-Bold.ttf'], ['PoppinsMed', 'fonts/Poppins-Medium.ttf'],
];

const useFonts = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all(FONTS.map(([n, f]) => new FontFace(n, `url(${staticFile(f)})`).load().then((ff) => (document.fonts as any).add(ff))))
      .then(() => continueRender(h)).catch((e) => { console.error(e); continueRender(h); });
  }, [h]);
};

// ------------------------------------------------------------------ helpers
const ease = (x: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
const useT = () => { const f = useCurrentFrame(); const {fps} = useVideoConfig(); return f / fps; };
/** 0→1 over d seconds starting at t0 (absolute opener time) */
const appear = (t: number, t0: number, d = 0.35) => ease((t - t0) / d);
/** springy pop in for stamps */
const pop = (t: number, t0: number, fps: number) => (t < t0 ? 0 : spring({frame: Math.round((t - t0) * fps), fps, config: {damping: 11, stiffness: 180, mass: 0.6}}));

const Grain: React.FC<{o?: number}> = ({o = 0.22}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'overlay', opacity: o}}>
      <svg width="1920" height="1080">
        <filter id={`g${f % 4}`}><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={f % 4} /><feColorMatrix type="saturate" values="0" /></filter>
        <rect width="1920" height="1080" filter={`url(#g${f % 4})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** grayscale, high-contrast image with a halftone dot screen on top (zine / collage look) */
const Halftone: React.FC<{src: string; style?: React.CSSProperties; dot?: number; tint?: string}> = ({src, style, dot = 7, tint}) => (
  <div style={{position: 'absolute', overflow: 'hidden', ...style}}>
    <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(1) brightness(1.8) contrast(1.5)'}} />
    <div style={{position: 'absolute', inset: 0, backgroundImage: `radial-gradient(circle, rgba(0,0,0,.55) ${dot * 0.28}px, transparent ${dot * 0.36}px)`, backgroundSize: `${dot}px ${dot}px`, mixBlendMode: 'multiply'}} />
    {tint && <div style={{position: 'absolute', inset: 0, background: tint, mixBlendMode: 'multiply'}} />}
  </div>
);

const Tape: React.FC<{x: number; y: number; r?: number; w?: number}> = ({x, y, r = -6, w = 130}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: 38, background: 'rgba(214,190,140,.78)', transform: `rotate(${r}deg)`, boxShadow: '0 2px 4px rgba(0,0,0,.25)'}} />
);

const Stamp: React.FC<{text: string; t: number; at: number; x: number; y: number; r?: number; color?: string; size?: number; onDark?: boolean}> = ({text, t, at, x, y, r = -8, color = C.red, size = 54, onDark = false}) => {
  const {fps} = useVideoConfig(); const p = pop(t, at, fps); if (p <= 0) return null;
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) rotate(${r}deg) scale(${2.2 - 1.2 * p})`, opacity: Math.min(1, p * 1.4),
      border: `6px solid ${color}`, color, fontFamily: 'Anton', fontSize: size, letterSpacing: 3, padding: '4px 22px', whiteSpace: 'nowrap', mixBlendMode: onDark ? 'normal' : 'multiply', background: onDark ? 'rgba(10,10,14,.55)' : 'transparent', boxShadow: onDark ? '0 10px 30px rgba(0,0,0,.6)' : 'none'}}>{text}</div>
  );
};

// ------------------------------------------------------------------ beats
const FrontPage: React.FC<{b: Beat; t: number}> = ({b, t}) => {
  const {fps} = useVideoConfig();
  const slide = appear(t, b.from, 0.45);
  const lines: (At & {text: string; color?: string})[] = b.headline || [];
  return (
    <AbsoluteFill style={{background: '#1b1712'}}>
      <div style={{position: 'absolute', left: 150, top: 108 + (1 - slide) * 900, width: 1620, height: 1100, background: C.paper, transform: `rotate(${-1.2 + (1 - slide) * 6}deg)`, boxShadow: '0 30px 80px rgba(0,0,0,.6)', padding: '36px 60px', color: C.ink}}>
        <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'Typewriter', fontSize: 24, borderBottom: `3px solid ${C.ink}`, paddingBottom: 8}}>
          <span>{b.left || 'VOL. 1 · NO. 5'}</span><span>{b.date || ''}</span><span>{b.right || 'PRICE: ONE COFFEE'}</span>
        </div>
        <div style={{fontFamily: 'Fraktur', fontSize: 132, textAlign: 'center', lineHeight: 1.05, marginTop: 6}}>{b.masthead || 'The On-Call Times'}</div>
        <div style={{borderTop: `6px double ${C.ink}`, borderBottom: `2px solid ${C.ink}`, fontFamily: 'Typewriter', fontSize: 24, textAlign: 'center', padding: '6px 0', letterSpacing: 4}}>{b.tagline || 'ALL THE INCIDENTS FIT TO PRINT'}</div>
        <div style={{display: 'flex', gap: 40, marginTop: 26}}>
          <div style={{flex: 1.6}}>
            {lines.map((ln, i) => {
              const a = pop(t, ln.at, fps);
              return <div key={i} style={{fontFamily: 'Anton', fontSize: b.size || 150, lineHeight: 0.98, letterSpacing: 2, color: ln.color ? col(ln.color) : C.ink, opacity: a > 0 ? 1 : 0, transform: `scale(${1.25 - 0.25 * a})`, transformOrigin: 'left center'}}>{ln.text}</div>;
            })}
            {b.deck && <div style={{fontFamily: 'Abril', fontSize: 40, marginTop: 18, opacity: appear(t, b.deckAt ?? b.from + 0.6)}}>{b.deck}</div>}
            {/* body columns: grey bars, not readable copy */}
            <div style={{display: 'flex', gap: 24, marginTop: 22}}>
              {[0, 1, 2].map((c) => <div key={c} style={{flex: 1}}>{Array.from({length: 7}).map((_, k) => <div key={k} style={{height: 11, margin: '10px 0', background: '#b9ad93', width: `${78 + ((c * 7 + k) * 37) % 22}%`}} />)}</div>)}
            </div>
          </div>
          <div style={{flex: 1, position: 'relative', height: 520}}>
            {b.art && <Halftone src={b.art} style={{left: 0, top: 0, width: '100%', height: 420, border: `3px solid ${C.ink}`}} tint="#d9cba8" />}
            <div style={{position: 'absolute', top: 432, fontFamily: 'Typewriter', fontSize: 24}}>{b.caption || ''}</div>
          </div>
        </div>
      </div>
      {b.stamp && <Stamp text={b.stamp.text} t={t} at={b.stamp.at} x={1500} y={420} r={-10} size={64} />}
    </AbsoluteFill>
  );
};

const Dossier: React.FC<{b: Beat; t: number}> = ({b, t}) => {
  const cards = b.cards || [];
  return (
    <AbsoluteFill style={{background: '#0d0d10'}}>
      {/* collage wall */}
      {(b.wall || []).map((src: string, i: number) => <Halftone key={i} src={src} dot={6} style={{left: (i % 4) * 490 - 30, top: Math.floor(i / 4) * 560 - 40, width: 520, height: 600, opacity: 0.32, transform: `rotate(${(i % 3) - 1}deg)`}} />)}
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(10,10,14,.35), rgba(10,10,14,.85))'}} />
      <div style={{position: 'absolute', left: 120, top: 110, fontFamily: 'VT', fontSize: 40, color: C.green, opacity: appear(t, b.from)}}>{b.kicker || '> SUBJECT FILES · 3 MATCHES'}</div>
      {cards.map((c: any, i: number) => {
        const a = appear(t, c.at, 0.4); const x = 120 + i * 580; const cc = col(c.color);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: 190 + (1 - a) * 60, width: 520, height: 600, opacity: a, background: '#111317', border: `2px solid ${cc}`, transform: `rotate(${[-2, 1, -1][i % 3]}deg)`, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>
            {c.art && <Halftone src={c.art} dot={7} style={{left: 0, top: 0, width: 520, height: 250}} tint={cc} />}
            <div style={{position: 'absolute', left: 26, top: 262, fontFamily: 'Anton', fontSize: 84, color: C.white, letterSpacing: 2}}>{c.title}</div>
            <div style={{position: 'absolute', left: 28, top: 372, fontFamily: 'VT', fontSize: 34, color: cc}}>{c.sub}</div>
            {(c.fields || []).map(([k, v]: [string, string], j: number) => (
              <div key={j} style={{position: 'absolute', left: 28, top: 420 + j * 44, fontFamily: 'VT', fontSize: 32, color: C.muted, width: 470, display: 'flex', justifyContent: 'space-between'}}><span>{k}</span><span style={{color: C.white}}>{v}</span></div>
            ))}
          </div>
        );
      })}
      {(b.stamps || []).map((s: any, i: number) => <Stamp key={i} text={s.text} t={t} at={s.at} x={s.x ?? 960} y={s.y ?? 480 + i * 120} r={s.r ?? -6 + i * 5} size={64} onDark />)}
    </AbsoluteFill>
  );
};

const Board: React.FC<{b: Beat; t: number}> = ({b, t}) => {
  const {fps} = useVideoConfig();
  const cards = b.cards || []; const labels = b.labels || [];
  const cx = (i: number) => 380 + i * 580;
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 40%, #c79d63, ${C.kraft} 55%, #8a6438)`}}>
      {/* faint notebook rules */}
      <AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(0deg, rgba(60,40,20,.10) 0 2px, transparent 2px 46px)'}} />
      {cards.map((c: any, i: number) => {
        const a = pop(t, c.at, fps); if (a <= 0) return null;
        return (
          <div key={i} style={{position: 'absolute', left: cx(i) - 210, top: 90, width: 420, height: 330, background: C.paper, transform: `rotate(${[-4, 2, -2][i % 3]}deg) scale(${1.3 - 0.3 * a})`, boxShadow: '0 12px 26px rgba(0,0,0,.35)', padding: 18}}>
            {c.art && <Halftone src={c.art} dot={6} style={{left: 18, top: 18, width: 384, height: 200}} tint="#e9dcc0" />}
            <div style={{position: 'absolute', left: 0, right: 0, top: 232, textAlign: 'center', fontFamily: 'Marker', fontSize: 62, color: C.ink}}>{c.title}</div>
            <Tape x={150} y={-18} r={[-5, 4, -3][i % 3]} />
          </div>
        );
      })}
      <svg width="1920" height="1080" style={{position: 'absolute', left: 0, top: 0}}>
        {labels.map((l: any, i: number) => {
          const p = ease((t - l.at + 0.55) / 0.5); if (p <= 0) return null;
          const x0 = cx(l.card ?? i), y0 = 420, x1 = cx(l.card ?? i) + [-30, 20, -40][i % 3], y1 = [640, 750, 640][i % 3];
          return <line key={i} x1={x0} y1={y0} x2={x0 + (x1 - x0) * p} y2={y0 + (y1 - y0) * p} stroke={C.red} strokeWidth={6} strokeLinecap="round" />;
        })}
        {labels.map((l: any, i: number) => (t > l.at - 0.6 ? <circle key={'p' + i} cx={cx(l.card ?? i)} cy={420} r={13} fill={C.red} /> : null))}
      </svg>
      {labels.map((l: any, i: number) => {
        const a = pop(t, l.at, fps); if (a <= 0) return null;
        return (
          <div key={i} style={{position: 'absolute', left: cx(l.card ?? i) + [-30, 20, -40][i % 3], top: [690, 800, 690][i % 3], transform: `translate(-50%,-50%) rotate(${[-3, 3, -2][i % 3]}deg) scale(${1.4 - 0.4 * a})`, fontFamily: 'Marker', fontSize: 68, color: C.ink, whiteSpace: 'nowrap', background: 'rgba(255,248,220,.82)', padding: '2px 26px', boxShadow: '0 8px 18px rgba(0,0,0,.25)'}}>{l.text}</div>
        );
      })}
      {b.question && t > b.question.at && (
        <div style={{position: 'absolute', right: 150, top: 600, fontFamily: 'Marker', fontSize: 240, color: C.red, transform: `rotate(8deg) scale(${1.3 - 0.3 * pop(t, b.question.at, fps)})`, lineHeight: 1}}>{b.question.text || '?'}</div>
      )}
      <AbsoluteFill style={{boxShadow: 'inset 0 0 240px rgba(40,20,5,.65)'}} />
    </AbsoluteFill>
  );
};

const Photo: React.FC<{b: Beat; t: number}> = ({b, t}) => {
  const {fps} = useVideoConfig();
  const a = appear(t, b.from, 0.5); const big = pop(t, b.bigAt ?? b.from + 0.2, fps);
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 70% 45%, #1c2747, ${C.navy} 65%)`}}>
      <div style={{position: 'absolute', left: 60, top: 150, fontFamily: 'Anton', fontSize: 430, lineHeight: 0.86, color: 'transparent', WebkitTextStroke: `4px ${col(b.color || 'warm')}`, opacity: big, transform: `scale(${1.15 - 0.15 * big})`, transformOrigin: 'left center', letterSpacing: 4}}>{b.big}</div>
      <div style={{position: 'absolute', left: 60, top: 150, fontFamily: 'Anton', fontSize: 430, lineHeight: 0.86, color: col(b.color || 'warm'), opacity: big * 0.9, clipPath: `inset(${100 - 100 * ease((t - (b.bigAt ?? b.from)) / 0.8)}% 0 0 0)`, letterSpacing: 4}}>{b.big}</div>
      {b.photo && <Img src={staticFile(b.photo)} style={{position: 'absolute', right: 120, bottom: -40, height: 1040, transform: `translateY(${(1 - a) * 80}px) scale(${1.0 + 0.03 * ((t - b.from) / Math.max(1, b.to - b.from))})`, opacity: a, filter: 'drop-shadow(0 30px 40px rgba(0,0,0,.55))'}} />}
      <div style={{position: 'absolute', left: 70, top: 640, opacity: appear(t, b.from + 0.5)}}>
        {(b.small || []).map((s: string, i: number) => <div key={i} style={{fontFamily: 'Bebas', fontSize: 64, color: [C.cyan, C.amber, C.violet][i % 3], letterSpacing: 6, lineHeight: 1.05}}>{s}</div>)}
      </div>
      <div style={{position: 'absolute', left: 70, top: 880, fontFamily: 'Typewriter', fontSize: 30, color: C.white, opacity: appear(t, b.from + 0.8)}}>{b.name}<br /><span style={{color: C.muted}}>{b.role}</span></div>
    </AbsoluteFill>
  );
};

const Poster: React.FC<{b: Beat; t: number}> = ({b, t}) => {
  const {fps} = useVideoConfig();
  const lines: (At & {text: string; color?: string})[] = b.lines || [];
  return (
    <AbsoluteFill style={{background: b.bg === 'paper' ? C.paper : C.navy}}>
      {b.art && <Halftone src={b.art} dot={8} style={{left: 0, top: 0, width: 1920, height: 1080, opacity: 0.18}} />}
      {/* tri-colour vertical bars, brand signature */}
      {[C.cyan, C.amber, C.violet].map((c, i) => (
        <div key={i} style={{position: 'absolute', left: 1380 + i * 120, top: 0, width: 84, height: 1080 * ease((t - b.from - i * 0.08) / 0.6), background: c, opacity: 0.9}} />
      ))}
      <div style={{position: 'absolute', left: 110, top: 120}}>
        {lines.map((ln, i) => {
          const a = pop(t, ln.at, fps);
          return <div key={i} style={{fontFamily: 'Anton', fontSize: b.size || 250, lineHeight: 0.9, letterSpacing: 3, color: ln.color ? col(ln.color) : (b.bg === 'paper' ? C.ink : C.white), opacity: a > 0 ? 1 : 0, transform: `translateY(${(1 - a) * 60}px)`}}>{ln.text}</div>;
        })}
      </div>
      <div style={{position: 'absolute', left: 116, bottom: 150, display: 'flex', gap: 40, opacity: appear(t, b.smallAt ?? b.from + 0.8)}}>
        {(b.small || []).map((s: string, i: number) => <div key={i} style={{fontFamily: 'Bebas', fontSize: 54, letterSpacing: 6, color: [C.cyan, C.amber, C.violet][i % 3]}}>{s}</div>)}
      </div>
    </AbsoluteFill>
  );
};

const BEATS: Record<string, React.FC<{b: Beat; t: number}>> = {frontpage: FrontPage, dossier: Dossier, board: Board, photo: Photo, poster: Poster};

// ------------------------------------------------------------------ chrome: brand bug, captions, flash
const Brand: React.FC<{show: string; badge: string; dark: boolean}> = ({show, badge, dark}) => (
  <>
    <div style={{position: 'absolute', left: 60, top: 34, fontFamily: 'Poppins', fontSize: 30, color: dark ? C.ink : C.white}}>{'>_ Tech-dev'} <span style={{fontFamily: 'PoppinsMed', fontSize: 24, color: dark ? '#5b5446' : C.muted, marginLeft: 14}}>{show}</span></div>
    {badge && <div style={{position: 'absolute', right: 60, top: 28, fontFamily: 'Poppins', fontSize: 26, color: C.amber, border: `2px solid ${C.amber}`, background: 'rgba(6,12,30,.8)', padding: '6px 20px', borderRadius: 6}}>{badge}</div>}
  </>
);

const Captions: React.FC<{words: Word[]; t: number}> = ({words, t}) => {
  // chunks of up to 4 words, broken at punctuation
  const chunks: Word[][] = []; let cur: Word[] = [];
  words.forEach((w) => { cur.push(w); if (cur.length >= 4 || /[.,?!]$/.test(w.w)) { chunks.push(cur); cur = []; } });
  if (cur.length) chunks.push(cur);
  const ch = chunks.find((c, i) => t >= c[0].s - 0.08 && t < (chunks[i + 1] ? chunks[i + 1][0].s - 0.08 : c[c.length - 1].e + 0.4));
  if (!ch) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 64, display: 'flex', justifyContent: 'center'}}>
      <div style={{background: 'rgba(4,8,20,.82)', borderRadius: 18, padding: '12px 34px', fontFamily: 'Poppins', fontSize: 52, color: C.white, display: 'flex', gap: 16}}>
        {ch.map((w, i) => {
          const on = t >= w.s - 0.03 && t < w.e + 0.08;
          return <span key={i} style={{color: on ? C.amber : C.white, transform: `scale(${on ? 1.08 : 1})`, display: 'inline-block'}}>{w.w.replace(/[,]$/, '')}</span>;
        })}
      </div>
    </div>
  );
};

export const Opener: React.FC<OpenerProps> = (p) => {
  useFonts();
  const t = useT(); const {fps} = useVideoConfig();
  const bi = p.beats.findIndex((b) => t >= b.from && t < b.to);
  const b = p.beats[bi < 0 ? p.beats.length - 1 : bi];
  const Comp = b ? BEATS[b.type] : null;
  const lt = b ? t - b.from : 0;
  const jolt = b ? 1.06 - 0.06 * ease(lt / 0.35) + 0.025 * Math.min(1, lt / Math.max(1, b.to - b.from)) : 1;
  const flash = b && bi > 0 ? Math.max(0, 1 - lt / 0.12) : 0;
  const dark = b ? ['board'].includes(b.type) || (b.type === 'poster' && b.bg === 'paper') : false;
  const fadeOut = interpolate(t, [p.duration - 0.35, p.duration], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${jolt})`, opacity: fadeOut}}>{Comp && <Comp b={b} t={t} />}</AbsoluteFill>
      <Grain o={dark ? 0.28 : 0.18} />
      <AbsoluteFill style={{opacity: fadeOut}}>
        <Brand show={p.show} badge={p.badge} dark={dark} />
        <Captions words={p.words} t={t} />
      </AbsoluteFill>
      {flash > 0 && <AbsoluteFill style={{background: '#fff', opacity: flash * 0.55}} />}
      {p.voice && <Sequence from={Math.round((p.voiceAt || 0) * fps)}><Audio src={staticFile(p.voice)} /></Sequence>}
      {p.music && <Audio src={staticFile(p.music)} volume={(f) => 0.10 * Math.min(1, f / 15) * interpolate(f / fps, [p.duration - 0.8, p.duration], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} />}
      {(p.sfx || []).map((s, i) => <Sequence key={i} from={Math.max(0, Math.round(s.at * fps))}><Audio src={staticFile(s.file)} volume={s.vol ?? 0.5} /></Sequence>)}
    </AbsoluteFill>
  );
};
