// Tech-dev 3D hook opener: shots are built from data/opener.json (made by prep.py from the episode spec), so a daily
// task only writes beats with word anchors, never JavaScript. Beat types:
//   room     · wide ops room, nameplates drop on `drops` [t, t, t]
//   racks    · dolly down the server aisle, `pill` {text, at, color}
//   cloud    · orbit the clay cloud, `pill`
//   pipeline · track along the CI/CD conveyor, `pill`
//   desk     · close on desk `i` (engineer + wall screen), `pill`, screen animates
//   question · pull back to the whole room, coloured spots, big `text` (e.g. '?')
//   photo    · Shivam's cutout + slab text (`big` set in roles), `pill`
//   finale   · crane up over the room, `lines` [{text, at, color}] in big type, `small` [3]
import * as THREE from 'three';
import { ctx, W, H, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { T } from './core/timing.js';
import { camera } from './core/engine.js';
import { pill } from './core/look2d.js';
import { opsWorld, AREA, DESK_X } from './core/ops.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
const COL = { accent: '#38bdf8', warm: '#fbbf24', purple: '#a78bfa', ok: '#34d399', bad: '#f87171' };
const col = (c) => COL[c] || c || '#ffffff';

function bigLines(lines, t, x0 = 120, y0 = 210, size = 190) {
  ctx.save(); ctx.font = `${size}px Anton`; ctx.textBaseline = 'top'; ctx.lineJoin = 'round';
  lines.forEach((l, i) => {
    const k = eob(clamp((t - l.at) / 0.28)); if (t < l.at) return;
    ctx.globalAlpha = clamp((t - l.at) / 0.12); const y = y0 + i * size * 0.95 + (1 - k) * 50;
    ctx.lineWidth = 16; ctx.strokeStyle = 'rgba(5,8,20,0.85)'; ctx.strokeText(l.text, x0, y); ctx.fillStyle = col(l.color); ctx.fillText(l.text, x0, y);
  });
  ctx.restore();
}

export function buildShots(E) {
  const S = [], CUES = [], cue = (t, type, o = {}) => CUES.push({ t: +Math.max(0, t).toFixed(3), type, ...o });
  const D = window.OPENER;               // data/opener.json
  const cam = camera(32);
  const Wd = opsWorld(E, Object.assign(D.roles.map((r) => ({ ...r, color: col(r.color) })), { big: D.big || '5 YEARS' }), D.photo ? 'photo/' + D.photo : null);
  const LOOK = { aperture: 0.0022, maxblur: 0.009, bloom: 0.3, bloomThreshold: 0.82, vignette: 0.38, grain: 0.03, warm: 0.02, exposure: 1.3 };
  const render = (focusPt, extra = {}) => E.render(Wd.scene, cam, { ...LOOK, focus: cam.position.distanceTo(focusPt), ...extra });
  const resetPlates = () => Wd.desks.forEach((d) => d.plate.position.y = 0.86);
  const seatAll = (t) => Wd.desks.forEach((d, i) => Wd.seat(d.h, t + i, [Math.sin(t * 0.7 + i) * 8, 0]));
  const pillAt = (p, t, x = W / 2, y = 150) => { if (p && t >= p.at) pill(p.text, x, y, eob(seg(t, p.at, p.at + 0.25)), col(p.color || 'warm'), 'rgba(6,10,24,0.85)', 66); };

  D.beats.forEach((b, bi) => {
    const add = (draw, note) => S.push({ id: `B${bi + 1}`, at: b.from, note: note || b.type, draw });
    if (bi > 0) cue(b.from - 0.18, 'whoosh', { gain: 0.6 });
    if (b.type === 'room') {
      (b.drops || []).forEach((t) => cue(t + 0.22, 'thud', { gain: 0.7 }));
      add((lt, d, t, blit) => {
        Wd.update(t); seatAll(t); Wd.aim(0, 0);
        Wd.desks.forEach((dk, i) => { const t0 = (b.drops || [])[i] ?? b.from; const k = clamp((t - t0) / 0.32); dk.plate.position.y = t < t0 ? 9 : 0.86 + (1 - eob(k)) * 1.4; dk.plate.rotation.z = (1 - k) * 0.4; });
        cam.position.copy(lerpV(V3(0, 3.1, 7.4), V3(0, 1.9, 5.2), eio(lt / d))); cam.lookAt(0, 1.25, -0.4); render(V3(0, 1.1, 0)); blit();
      });
    } else if (b.type === 'racks') {
      add((lt, d, t, blit) => {
        Wd.update(t); Wd.aim(AREA.RACKS[0], 0); const [x, , z] = AREA.RACKS;
        cam.position.copy(lerpV(V3(x - 0.25, 1.35, z + 5.5), V3(x + 0.2, 1.5, z + 1.2), eio(lt / d))); cam.lookAt(x, 1.2, z - 3);
        render(V3(x, 1.2, z - 1), { aperture: 0.003, bloom: 0.55, bloomThreshold: 0.6 }); blit(); pillAt(b.pill, t);
      });
      if (b.pill) cue(b.pill.at, 'pop', { gain: 0.6 });
    } else if (b.type === 'cloud') {
      add((lt, d, t, blit) => {
        Wd.update(t); Wd.aim(AREA.CLOUD[0], 0); const [x, , z] = AREA.CLOUD, a = lerp(-0.5, 0.45, eio(lt / d));
        cam.position.set(x + Math.sin(a) * 4.6, 2.3 + 0.3 * eio(lt / d), z + Math.cos(a) * 4.6); cam.lookAt(x, 1.8, z);
        render(V3(x, 2, z), { bloom: 0.2, exposure: 0.9 }); blit(); pillAt(b.pill, t);
      });
      if (b.pill) cue(b.pill.at, 'pop', { gain: 0.6 });
    } else if (b.type === 'pipeline') {
      add((lt, d, t, blit) => {
        Wd.update(t); Wd.aim(0, AREA.PIPE[2]); const [x, , z] = AREA.PIPE, k = eio(lt / d);
        cam.position.set(x - 3.2 + 4.4 * k, 1.75, z + 3.4); cam.lookAt(x - 1.6 + 4.4 * k, 1.0, z);
        render(V3(x - 1.6 + 4.4 * k, 1, z), { aperture: 0.0028 }); blit(); pillAt(b.pill, t);
      });
      if (b.pill) cue(b.pill.at, 'pop', { gain: 0.6 });
    } else if (b.type === 'desk') {
      const i = b.i ?? 0, x = DESK_X[i];
      add((lt, d, t, blit) => {
        Wd.update(t); seatAll(t); resetPlates(); Wd.aim(x, 0);
        const dk = Wd.desks[i]; Wd.redraw(dk.tex, clamp((t - b.from) / Math.max(0.8, (b.pill?.at ?? b.to) - b.from + 0.6)));
        const s = b.side ?? (i === 0 ? 1 : i === 2 ? -1 : 0.6);
        cam.position.copy(lerpV(V3(x + 1.5 * s, 1.55, 2.9), V3(x + 0.7 * s, 1.5, 2.1), eio(lt / d))); cam.lookAt(x, 1.55, -1.1);
        render(V3(x, 1.4, -0.6), { aperture: 0.003 }); blit(); pillAt(b.pill, t, W / 2 + (s > 0 ? -380 : 380), 170);
      });
      if (b.pill) cue(b.pill.at, 'pop', { gain: 0.6 });
    } else if (b.type === 'question') {
      add((lt, d, t, blit) => {
        Wd.update(t); seatAll(t); resetPlates(); Wd.aim(0, 0);
        Wd.desks.forEach((dk) => dk.light.intensity = 6 + 6 * Math.max(0, Math.sin(t * 6)));
        cam.position.copy(lerpV(V3(0, 1.7, 3.6), V3(0, 2.4, 6.4), eo(lt / d))); cam.lookAt(0, 1.3, -0.6); render(V3(0, 1.2, 0)); blit();
        Wd.desks.forEach((dk) => dk.light.intensity = 6);
        if (b.text && t >= (b.at ?? b.from)) { ctx.save(); const k = eob(clamp((t - (b.at ?? b.from)) / 0.3)); ctx.font = '300px Anton'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 18; ctx.strokeStyle = 'rgba(5,8,20,.9)'; ctx.translate(W - 220, 470); ctx.scale(k, k); ctx.rotate(0.12); ctx.strokeText(b.text, 0, 0); ctx.fillStyle = '#f87171'; ctx.fillText(b.text, 0, 0); ctx.restore(); }
      });
      if (b.at) cue(b.at, 'pop', { gain: 0.8 });
    } else if (b.type === 'photo') {
      add((lt, d, t, blit) => {
        Wd.update(t); Wd.aim(0, AREA.PHOTO[2]); const [x, , z] = AREA.PHOTO, k = eio(lt / d);
        const rise = eob(clamp((t - (b.bigAt ?? b.from)) / 0.4)); Wd.slab.position.y = 1.75 - (1 - rise) * 1.2; Wd.slab.visible = t >= (b.bigAt ?? b.from) - 0.05;
        cam.position.set(x + lerp(-0.5, 0.4, k), 1.45, z + lerp(4.0, 3.3, k)); cam.lookAt(x + 0.15, 1.35, z - 0.6);
        render(V3(x + 0.55, 1.3, z - 0.2), { aperture: 0.002 }); blit();
        if (b.name && t >= b.from + 0.4) { ctx.save(); ctx.globalAlpha = clamp((t - b.from - 0.4) / 0.3); ctx.font = '800 34px Inter'; ctx.fillStyle = '#ffffff'; ctx.fillText(b.name, 110, H - 230); ctx.font = '600 28px Inter'; ctx.fillStyle = '#94a3b8'; ctx.fillText(b.role || '', 110, H - 190); ctx.restore(); }
      });
      if (b.bigAt) cue(b.bigAt, 'thud', { gain: 0.8 });
    } else if (b.type === 'finale') {
      (b.lines || []).forEach((l) => cue(l.at, 'thud', { gain: 0.6 }));
      add((lt, d, t, blit) => {
        Wd.update(t); seatAll(t); resetPlates(); Wd.aim(0, 0); const k = eio(lt / d);
        cam.position.set(lerp(2.8, 3.6, k), lerp(1.8, 3.6, k), lerp(5.2, 6.2, k)); cam.lookAt(0.9, 1.2, -0.6);
        render(V3(0, 1.2, 0), { vignette: 0.6 }); blit();
        ctx.save(); ctx.globalAlpha = 0.55; const g = ctx.createLinearGradient(0, 0, W * 0.65, 0); g.addColorStop(0, 'rgba(5,8,20,0.95)'); g.addColorStop(1, 'rgba(5,8,20,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
        bigLines(b.lines || [], t, 110, 170, 190);
        if (b.small && t >= (b.smallAt ?? b.from + 0.5)) { ctx.save(); ctx.font = '62px Anton'; ctx.globalAlpha = clamp((t - (b.smallAt ?? b.from + 0.5)) / 0.3); let xx = 116; b.small.forEach((s, j) => { ctx.fillStyle = ['#38bdf8', '#fbbf24', '#a78bfa'][j % 3]; ctx.fillText(s, xx, 800); xx += ctx.measureText(s).width + 50; }); ctx.restore(); }
      });
    }
  });

  // brand bug + badge on every frame (wrap each shot's draw)
  S.forEach((s) => { const f = s.draw; s.draw = (lt, d, t, blit) => { f(lt, d, t, blit); brand(); }; });
  function brand() {
    ctx.save(); ctx.font = '800 30px Inter'; ctx.fillStyle = '#ffffff'; ctx.textBaseline = 'top'; ctx.fillText('>_ Tech-dev', 60, 36);
    const w = ctx.measureText('>_ Tech-dev').width; ctx.font = '600 24px Inter'; ctx.fillStyle = '#cbd5e1'; ctx.fillText(D.show || '', 60 + w + 16, 42);
    if (D.badge) { ctx.font = '800 26px Inter'; const bw = ctx.measureText(D.badge).width + 40; ctx.fillStyle = 'rgba(6,12,30,0.85)'; ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 2; ctx.beginPath(); ctx.roundRect(W - 60 - bw, 28, bw, 52, 6); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#fbbf24'; ctx.fillText(D.badge, W - 60 - bw + 20, 40); }
    ctx.restore();
  }
  return { shots: S, cues: CUES };
}
