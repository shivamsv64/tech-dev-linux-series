// Tech-dev 3D world for the hook opener: a clay-style ops room (three engineers at desks, each with a big wall screen
// and a nameplate), a server-rack aisle, a floating cloud with orbiting containers, a CI/CD conveyor with gates, and a
// photo stage for Shivam's real cutout with extruded "slab" type. Everything is built once; update(t) animates it.
// Areas sit far apart on one floor (fog hides the others): ROOM (0,0,0) · RACKS (-14,0,0) · CLOUD (14,0,0) ·
// PIPE (0,0,14) · PHOTO (0,0,28).
import * as THREE from 'three';
import { rbox, sphere, smin, capsule, mesh } from './sdf.js';
import { lightRig } from './engine.js';
import { Human } from './human.js';

export const AREA = { ROOM: [0, 0, 0], RACKS: [-14, 0, 0], CLOUD: [14, 0, 0], PIPE: [0, 0, 14], PHOTO: [0, 0, 28] };
export const DESK_X = [-2.6, 0, 2.6];
const std = (color, rough = 0.6, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, ...extra });
const glow = (map, k = 1) => new THREE.MeshBasicMaterial({ map, toneMapped: false, color: new THREE.Color(k, k, k) });
const shadowed = (m) => { m.castShadow = true; m.receiveShadow = true; return m; };
const sdfMesh = (f, b, step, mat) => shadowed(new THREE.Mesh(mesh(f, b, step), mat));
export function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.userData = { c, draw }; return t;
}
const redraw = (tex, ...a) => { const { c, draw } = tex.userData; draw(c.getContext('2d'), c.width, c.height, ...a); tex.needsUpdate = true; };

// ---------------------------------------------------------------- screen content (drawn on canvases)
function screenDraw(kind, col, label) {
  return (g, w, h, k = 1) => {               // k 0..1 = how far the animation has played
    g.fillStyle = '#060b18'; g.fillRect(0, 0, w, h);
    g.strokeStyle = col; g.globalAlpha = 0.25; g.lineWidth = 1;
    for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
    for (let y = 0; y < h; y += 32) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    g.globalAlpha = 1; g.fillStyle = col; g.font = '800 34px Inter'; g.fillText(label, 26, 50);
    if (kind === 'graph') {                       // uptime line with a dip, drawn left → right
      g.lineWidth = 6; g.strokeStyle = '#34d399'; g.beginPath();
      const n = 60, m = Math.floor(n * k);
      for (let i = 0; i <= m; i++) { const x = 30 + i * (w - 60) / n, dip = i > 38 && i < 43 ? 120 : 0; const y = 120 + Math.sin(i * 0.9) * 6 + dip; i ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.stroke(); g.font = '900 64px Inter'; g.fillStyle = '#ffffff'; g.fillText('99.9%', w - 250, h - 40);
    } else if (kind === 'pipeline') {             // stages light up one by one
      const st = ['CODE', 'BUILD', 'TEST', 'DEPLOY'];
      st.forEach((s, i) => { const on = k * 4 > i; const x = 26 + i * (w - 52) / 4; g.fillStyle = on ? '#34d399' : '#1e293b'; g.beginPath(); g.roundRect(x, 140, (w - 52) / 4 - 18, 90, 14); g.fill(); g.fillStyle = on ? '#04120c' : '#64748b'; g.font = '800 30px Inter'; g.fillText(s, x + 16, 197); });
      g.font = '900 54px Inter'; g.fillStyle = '#ffffff'; g.fillText('12 deploys / week', 26, h - 40);
    } else if (kind === 'cost') {                 // cost bars grow, one red
      const v = [0.35, 0.5, 0.42, 0.7, 0.95, 0.6];
      v.forEach((f, i) => { const bh = (h - 170) * f * Math.min(1, k * 1.4); g.fillStyle = i === 4 ? '#f87171' : '#a78bfa'; g.fillRect(40 + i * 95, h - 50 - bh, 64, bh); });
      g.font = '900 54px Inter'; g.fillStyle = '#ffffff'; g.fillText('$ / month', w - 300, 120);
    } else if (kind === 'terminal') {
      g.font = '28px monospace'; g.fillStyle = '#34d399';
      ['$ kubectl get pods', 'api-7f9c   Running', 'web-2b1d   Running', '$ terraform plan', 'Plan: 2 to add'].slice(0, 1 + Math.floor(k * 5)).forEach((l, i) => g.fillText(l, 26, 100 + i * 44));
    }
  };
}

/** fake-extruded text: stacked transparent planes, bright front, darker back. Returns a Group (centred) */
export function slabText(text, { color = '#fbbf24', height = 1, layers = 12, depth = 0.012, font = 'Anton', w = 1024 } = {}) {
  const g = new THREE.Group();
  const cv = document.createElement('canvas'), x = cv.getContext('2d'); x.font = `${w * 0.36}px ${font}`;
  const tw = Math.ceil(x.measureText(text).width) + 40; cv.width = tw; cv.height = Math.ceil(w * 0.46);
  const ar = cv.width / cv.height;
  const make = (fill) => { const c = cv.cloneNode(); const y = c.getContext('2d'); y.font = `${w * 0.36}px ${font}`; y.textBaseline = 'middle'; y.fillStyle = fill; y.fillText(text, 20, c.height / 2); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; };
  const front = make(color), side = make(new THREE.Color(color).multiplyScalar(0.38).getStyle());
  for (let i = layers - 1; i >= 0; i--) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(height * ar, height), new THREE.MeshBasicMaterial({ map: i === 0 ? front : side, transparent: true, alphaTest: 0.5, toneMapped: false }));
    m.position.z = -i * depth; g.add(m);
  }
  return g;
}

// ---------------------------------------------------------------- the world
export function opsWorld(E, roles, photoUrl) {
  const scene = new THREE.Scene(); scene.environment = E.envMap; scene.environmentIntensity = 0.55;
  scene.background = new THREE.Color('#111a30'); scene.fog = new THREE.Fog('#111a30', 10, 26);
  const floorTex = canvasTex(1024, 1024, (g, w, h) => { g.fillStyle = '#1a2133'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(56,189,248,0.10)'; g.lineWidth = 3; for (let i = 0; i <= 8; i++) { g.beginPath(); g.moveTo(i * w / 8, 0); g.lineTo(i * w / 8, h); g.stroke(); g.beginPath(); g.moveTo(0, i * h / 8); g.lineTo(w, i * h / 8); g.stroke(); } });
  floorTex.wrapS = floorTex.wrapT = THREE.RepeatWrapping; floorTex.repeat.set(14, 14);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), std('#ffffff', 0.32, { map: floorTex, metalness: 0.25 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const L = lightRig(scene, { key: '#FFE2C4', keyI: 3.0, keyPos: [2, 5, 5], rimCol: '#9CC8FF', rimI: 2.0, sky: '#dbe8ff', ground: '#2a3550', hemiI: 1.1, shadowBox: 5, target: [0, 1, 0] });
  const aim = (x, z) => { L.key.position.set(x + 2, 5, z + 5); L.key.target.position.set(x, 1, z); L.key.target.updateMatrixWorld(); L.rim.position.set(x - 3, 3, z - 3); };

  // ── ROOM: back wall, desks, engineers, wall screens, nameplates
  const wall = shadowed(new THREE.Mesh(new THREE.BoxGeometry(12, 4.4, 0.2), std('#121a2e', 0.85))); wall.position.set(0, 2.2, -2.4); scene.add(wall);
  const deskMat = std('#9c7a5c', 0.55), legMat = std('#2b3550', 0.5), chairMat = std('#1f2937', 0.6);
  const desks = roles.map((r, i) => {
    const x = DESK_X[i], col = r.color;
    const top = sdfMesh((p) => rbox(p, [0, 0, 0], [0.78, 0.035, 0.38], 0.03), [[-0.82, -0.06, -0.42], [0.82, 0.06, 0.42]], 0.02, deskMat); top.position.set(x, 0.74, 0); scene.add(top);
    for (const sx of [-0.7, 0.7]) { const lg = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.72, 0.6), legMat)); lg.position.set(x + sx, 0.36, 0); scene.add(lg); }
    // laptop (back towards camera) with a glowing role-colour edge
    const base = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.02, 0.28), std('#9aa3b2', 0.35, { metalness: 0.6 }))); base.position.set(x, 0.78, -0.12); scene.add(base);
    const lid = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.28, 0.015), std('#9aa3b2', 0.35, { metalness: 0.6 }))); lid.position.set(x, 0.92, -0.02); lid.rotation.x = 0.25; scene.add(lid);
    const edge = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.012, 0.016), new THREE.MeshBasicMaterial({ color: col, toneMapped: false })); edge.position.set(x, 1.055, 0.015); edge.rotation.x = 0.25; scene.add(edge);
    // chair
    const seat = sdfMesh((p) => smin(rbox(p, [0, 0, 0], [0.24, 0.04, 0.22], 0.03), rbox(p, [0, 0.32, -0.21], [0.22, 0.26, 0.035], 0.03), 0.04), [[-0.3, -0.08, -0.3], [0.3, 0.62, 0.28]], 0.015, chairMat);
    seat.position.set(x, 0.47, -0.62); scene.add(seat);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.42, 12), legMat); post.position.set(x, 0.23, -0.62); scene.add(post);
    // engineer, seated behind the desk, facing the camera (+z)
    const h = new Human({ skin: r.skin || '#C68B67', shirt: r.shirt || col, pants: '#2B3550', hair: r.hair || '#1f1712' });
    h.group.position.set(x, 0, -0.6); h.hips.position.y = 0.66; scene.add(h.group);
    // wall screen behind (big, glowing) + its light
    const tex = canvasTex(640, 360, screenDraw(r.screen || 'graph', col, r.screenLabel || r.label));
    redraw(tex, 1);
    const frame = shadowed(new THREE.Mesh(new THREE.BoxGeometry(1.78, 1.04, 0.06), std('#0b0f1a', 0.4))); frame.position.set(x, 2.15, -2.26); scene.add(frame);
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(1.68, 0.945), glow(tex, 1.15)); scr.position.set(x, 2.15, -2.22); scene.add(scr);
    const pl = new THREE.PointLight(col, 6, 4.5, 2); pl.position.set(x, 2.0, -1.6); scene.add(pl);
    // nameplate on the desk front (drops in on cue)
    const plate = new THREE.Group();
    const ptex = canvasTex(512, 128, (g, w, hh) => { g.fillStyle = '#0b1120'; g.fillRect(0, 0, w, hh); g.fillStyle = col; g.fillRect(0, hh - 12, w, 12); g.font = '86px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#ffffff'; g.fillText(r.label, w / 2, hh / 2 - 4); });
    const pbody = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.18, 0.07), [std('#0b1120'), std('#0b1120'), std('#0b1120'), std('#0b1120'), new THREE.MeshStandardMaterial({ map: ptex, roughness: 0.4, emissive: '#ffffff', emissiveMap: ptex, emissiveIntensity: 0.55 }), std('#0b1120')]));
    plate.add(pbody); plate.position.set(x, 0.86, 0.28); scene.add(plate);
    return { x, h, tex, plate, light: pl, col, screen: r.screen || 'graph' };
  });

  // ── RACKS aisle
  const [rx, , rz] = AREA.RACKS, leds = [];
  const rackMat = std('#2a3446', 0.4, { metalness: 0.45 });
  for (const side of [-1, 1]) for (let i = 0; i < 9; i++) {
    const rk = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.7, 2.1, 0.9), rackMat)); rk.position.set(rx + side * 1.05, 1.05, rz - 4.5 + i * 1.0); scene.add(rk);
    for (let u = 0; u < 9; u++) {
      const c = ['#38bdf8', '#34d399', '#34d399', '#fbbf24'][(i * 7 + u * 3) % 4];
      const led = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.018, 0.06), new THREE.MeshBasicMaterial({ color: c, toneMapped: false }));
      led.position.set(rx + side * (1.05 - 0.36), 0.3 + u * 0.2, rz - 4.5 + i * 1.0 + ((u % 3) - 1) * 0.22); scene.add(led); leds.push(led);
    }
  }
  const aisleLight = new THREE.PointLight('#38bdf8', 9, 9, 2); aisleLight.position.set(rx, 2.6, rz); scene.add(aisleLight);
  const aisleLight2 = new THREE.PointLight('#cfe2ff', 6, 8, 2); aisleLight2.position.set(rx, 2.4, rz + 3.5); scene.add(aisleLight2);

  // ── CLOUD: a soft clay cloud with orbiting containers
  const [cx, , cz] = AREA.CLOUD;
  const cloud = sdfMesh((p) => [[0, 0, 0, 0.62], [0.6, -0.1, 0.05, 0.45], [-0.62, -0.12, 0, 0.42], [0.25, 0.32, -0.05, 0.42], [-0.28, 0.28, 0.05, 0.4], [0, -0.22, 0.2, 0.42]].reduce((d, s) => smin(d, sphere(p, s, s[3]), 0.2), 9),
    [[-1.2, -0.8, -0.8], [1.2, 0.9, 0.8]], 0.03, new THREE.MeshPhysicalMaterial({ color: '#aaa2db', roughness: 0.65, sheen: 0.5, sheenColor: new THREE.Color('#c4b5fd'), emissive: '#4c3fa0', emissiveIntensity: 0.05 }));
  cloud.position.set(cx, 2.0, cz); scene.add(cloud);
  const orbiters = ['#38bdf8', '#fbbf24', '#a78bfa', '#34d399', '#38bdf8', '#f87171'].map((c, i) => { const b = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.16, 0.16), std(c, 0.35, { emissive: c, emissiveIntensity: 0.25 }))); scene.add(b); return b; });
  const pad = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.7, 0.12, 48), std('#1e293b', 0.4, { metalness: 0.3 }))); pad.position.set(cx, 0.06, cz); scene.add(pad);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.62, 0.02, 8, 96), new THREE.MeshBasicMaterial({ color: '#a78bfa', toneMapped: false })); ring.rotation.x = Math.PI / 2; ring.position.set(cx, 0.13, cz); scene.add(ring);
  const cloudLight = new THREE.PointLight('#a78bfa', 4, 6, 2); cloudLight.position.set(cx, 3.4, cz + 1.2); scene.add(cloudLight);

  // ── PIPE: conveyor with packages through 3 gates
  const [px, , pz] = AREA.PIPE;
  const belt = shadowed(new THREE.Mesh(new THREE.BoxGeometry(9, 0.12, 0.8), std('#273449', 0.5))); belt.position.set(px, 0.7, pz); scene.add(belt);
  for (const sx of [-4.2, 4.2]) { const lg = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.7, 0.7), legMat)); lg.position.set(px + sx, 0.35, pz); scene.add(lg); }
  const gateNames = ['BUILD', 'TEST', 'DEPLOY'], gates = gateNames.map((n, i) => {
    const gx = px - 2.4 + i * 2.4, g = new THREE.Group(); g.position.set(gx, 0, pz);
    const mat = std('#334155', 0.45);
    for (const s of [-1, 1]) { const p = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.6, 0.12), mat)); p.position.set(0, 0.8, s * 0.55); g.add(p); }
    const beam = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.34, 1.24), mat)); beam.position.set(0, 1.72, 0); g.add(beam);
    const t = canvasTex(256, 64, (c, w, h) => { c.fillStyle = '#0b1120'; c.fillRect(0, 0, w, h); c.font = '44px Anton'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#fff'; c.fillText(n, w / 2, h / 2); });
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.25), glow(t, 1)); sign.position.set(0.09, 1.72, 0); sign.rotation.y = Math.PI / 2; g.add(sign);
    const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 12), new THREE.MeshBasicMaterial({ color: '#334155', toneMapped: false })); lamp.position.set(0, 1.98, 0); g.add(lamp);
    scene.add(g); return { g, lamp, x: gx };
  });
  const pkgs = Array.from({ length: 7 }, (_, i) => { const b = shadowed(new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.3, 0.34), std(['#c49460', '#b07d4c'][i % 2], 0.75))); scene.add(b); return b; });
  const pipeLight = new THREE.PointLight('#34d399', 7, 9, 2); pipeLight.position.set(px, 3, pz + 1.5); scene.add(pipeLight);
  const pipeFill = new THREE.PointLight('#fff1e2', 6, 9, 2); pipeFill.position.set(px - 2, 2.6, pz + 3); scene.add(pipeFill);

  // ── PHOTO stage: Shivam's real cutout on a glowing glass panel, slab text behind
  const [fx, , fz] = AREA.PHOTO;
  const back = new THREE.Mesh(new THREE.PlaneGeometry(12, 6), new THREE.MeshBasicMaterial({ color: '#0b1430' })); back.position.set(fx, 3, fz - 2.2); scene.add(back);
  ['#38bdf8', '#fbbf24', '#a78bfa'].forEach((c, i) => { const s = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 6), new THREE.MeshBasicMaterial({ color: c, toneMapped: false })); s.position.set(fx + 3.2 + i * 0.45, 3, fz - 2.1); scene.add(s); });
  const slab = slabText(roles.big || '5 YEARS', { color: '#fbbf24', height: 1.25, layers: 14, depth: 0.018 }); slab.position.set(fx - 0.2, 1.75, fz - 1.3); scene.add(slab);
  let photo = null;
  if (photoUrl) {
    const t = new THREE.TextureLoader().load(photoUrl); t.colorSpace = THREE.SRGBColorSpace;
    photo = new THREE.Mesh(new THREE.PlaneGeometry(1.45, 1.9), new THREE.MeshBasicMaterial({ map: t, transparent: true, alphaTest: 0.08, toneMapped: false }));
    photo.position.set(fx + 0.55, 0.95, fz - 0.2); scene.add(photo);
  }
  const photoLight = new THREE.PointLight('#fbbf24', 5, 6, 2); photoLight.position.set(fx - 1, 2.5, fz); scene.add(photoLight);

  return {
    scene, aim, desks, gates, slab, photo, cloud,
    update(t) {
      leds.forEach((l, i) => (l.visible = Math.sin(t * (3 + (i % 5)) + i * 1.7) > -0.55));
      orbiters.forEach((b, i) => { const a = t * 0.7 + i * Math.PI / 3, r = 1.45 + 0.1 * Math.sin(i); b.position.set(cx + Math.cos(a) * r, 2.0 + Math.sin(a * 1.3 + i) * 0.35, cz + Math.sin(a) * r); b.rotation.set(t + i, t * 0.7, 0); });
      cloud.position.y = 2.0 + Math.sin(t * 1.2) * 0.05;
      pkgs.forEach((b, i) => { const xx = ((t * 1.1 + i * 1.3) % 9) - 4.5; b.position.set(px + xx, 0.91, pz); });
      gates.forEach((gt) => { const near = pkgs.some((b) => Math.abs(b.position.x - gt.x) < 0.3); if (near) gt.lit = t; gt.lamp.material.color.set(t - (gt.lit ?? -9) < 0.6 ? '#34d399' : '#334155'); });
    },
    seat(h, typing = 0, look = [0, 0]) {       // seated pose; typing 0..1 animates the hands
      const s = Math.sin(typing * 40) * 4;
      h.pose({ hipL: [88, 0, 4], hipR: [88, 0, 4], knL: 86, knR: 86, spine: [6, 0, 0], head: [4 + look[1], look[0], 0], shL: [48 + s, 0, 10], shR: [48 - s, 0, 10], elL: 62, elR: 62 });
      h.hips.position.y = 0.66;
    },
    redraw,
  };
}
