// Sahne: koreografi, kamera, arka plan, aura, altyazılar.
"use strict";
(() => {
const { lerp, clamp, smooth, TAU } = window.CharUtil;
const W = 1080, H = 1920;
const BEAT = 0.5;
const TL = window.TIMELINE;            // build.py tarafından üretilir
const TOTAL = TL.total;
const sin = Math.sin, cos = Math.cos, PI = Math.PI;

// ---- yardımcılar -----------------------------------------------------------
function hash(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
const ease = (x) => smooth(0, 1, x);
function env(t, a, b, fadeIn = 0.3, fadeOut = 0.3) { return smooth(a, a + fadeIn, t) * (1 - smooth(b - fadeOut, b, t)); }

function voiceAt(t) {
  for (const k of Object.keys(TL.voice)) {
    const v = TL.voice[k];
    if (t >= v.start && t < v.start + v.dur) {
      const i = Math.floor((t - v.start) * 30);
      const e = v.env[Math.min(i, v.env.length - 1)] || 0;
      const e2 = v.env[Math.min(i + 1, v.env.length - 1)] || 0;
      return { key: k, local: t - v.start, amp: (e + e2) / 2 };
    }
  }
  return null;
}

// ---- pozlar ----------------------------------------------------------------
const BASE = {
  px: 0, py: 0, hip: 0, spine: 0, neck: 0, headX: 0, turn: 0,
  lSh: 0.12, rSh: 0.12, lEl: 0.05, rEl: 0.05, lWr: 0, rWr: 0,
  lFoot: [-78, 0], rFoot: [78, 0], lLift: 0, rLift: 0,
  smile: 0.6, mouth: 0, blink: 0, wink: 0, brow: 0, browUp: 0, blush: 0, pupil: 1,
  look: [0, 0], wings: 0, wingFlap: 0, flare: 0, wind: 0, flipX: 1,
};
function P(o) { return Object.assign({}, BASE, o); }
const hipHand = (p, s) => [p.px + s * 150, p.py - 905];

function idle(t) {
  return P({ py: 3 * sin(t * 2.2), hip: 0.02 * sin(t * 1.3), spine: -0.015 * sin(t * 1.3), neck: 0.04 * sin(t * 0.9) + 0.05,
             lSh: 0.14 + 0.02 * sin(t * 2.2), rSh: 0.14 + 0.02 * sin(t * 2.2 + 1) });
}

function intro(t) {
  const p = idle(t);
  const w = smooth(1.2, 2.0, t) * (1 - smooth(5.2, 6.2, t));
  p.lHand = hipHand(p, -1); p.lHandShape = "open";
  p.rSh = lerp(p.rSh, 0.28, w); p.rEl = lerp(p.rEl, 2.55 + 0.25 * sin(t * 8), w);
  p.neck = 0.09 + 0.03 * sin(t * 1.4);
  p.hip = 0.05; p.px = 10; p.lFoot = [-70, 0]; p.rFoot = [95, 0];
  p.smile = 0.75;
  return p;
}

function stepTouch(B, t, arms) {
  const s = sin(PI * B / 2), b = (1 - cos(TAU * B)) / 2;
  const p = P({ px: 55 * s, py: 16 * b, hip: -0.09 * s, spine: 0.11 * s, neck: -0.06 * s + 0.03 * sin(PI * B),
                lFoot: [-92, 0], rFoot: [92, 0],
                lLift: 26 * Math.max(0, s) ** 3, rLift: 26 * Math.max(0, -s) ** 3, smile: 0.8, look: [-s * 0.4, 0] });
  if (arms === "swing") {
    p.lSh = 0.3 + 0.55 * Math.max(0, -s); p.lEl = 0.9 + 0.5 * Math.max(0, -s);
    p.rSh = 0.3 + 0.55 * Math.max(0, s); p.rEl = 0.9 + 0.5 * Math.max(0, s);
    p.lHandShape = p.rHandShape = "fist";
  } else if (arms === "wave") {
    p.lSh = 2.45 + 0.25 * sin(PI * B); p.lEl = 0.35 * sin(PI * B + 1);
    p.rSh = 2.45 - 0.25 * sin(PI * B); p.rEl = -0.35 * sin(PI * B + 1);
    p.wind = 300 * s;
  }
  return p;
}

function clapUp(B) {
  const ph = B % 1, open = smooth(0, 0.5, ph) * (1 - smooth(0.5, 1, ph));
  const s = sin(PI * B / 2), b = (1 - cos(TAU * B)) / 2;
  const p = P({ px: 25 * s, py: 22 * b, hip: -0.05 * s, spine: 0.05 * s, lFoot: [-95, 0], rFoot: [95, 0], smile: 0.95, neck: 0.05 * sin(PI * B) });
  const y = p.py - 1590 + 40 * open;
  p.lHand = [p.px - 22 - 120 * open, y]; p.rHand = [p.px + 22 + 120 * open, y];
  p.lHandShape = p.rHandShape = "open";
  return p;
}

function bodyRoll(B) {
  const a = PI * B / 2;
  const p = P({ spine: 0.16 * sin(a), hip: -0.14 * sin(a - 0.9), neck: 0.13 * sin(a + 0.9), px: 35 * sin(a - 0.9), py: 10 + 10 * sin(a * 2),
                lFoot: [-88, 0], rFoot: [88, 0], smile: 0.7, blink: 0.25, look: [0.3, 0] });
  p.lHand = hipHand(p, -1);
  p.rSh = 1.3 + 0.9 * (0.5 + 0.5 * sin(a)); p.rEl = 1.3 - 0.6 * sin(a);
  p.wind = -200 * sin(a);
  return p;
}

function spin(B0, B) { // B0 başlangıç vuruşu, 2 vuruşluk dönüş
  const u = clamp((B - B0) / 2, 0, 1), e = ease(u);
  const p = P({ flipX: cos(TAU * e), flare: sin(PI * u) * 1.1, py: -10 * sin(PI * u), lSh: 1.25, rSh: 1.25, lEl: 0.3, rEl: 0.3,
                lFoot: [-60, 0], rFoot: [60, 0], rLift: 30 * sin(PI * u), smile: 0.9, turn: sin(TAU * e) * 0.6 });
  return p;
}

function pointPose(t, B) {
  const p = P({ px: 45, hip: -0.12, spine: 0.08, neck: -0.1, lFoot: [-70, 0], rFoot: [110, 0], smile: 0.85, wink: smooth(0.2, 0.35, (B % 4) / 4) * (1 - smooth(0.75, 0.9, (B % 4) / 4)) });
  p.lHand = hipHand(p, -1);
  p.rSh = 2.25; p.rEl = 0.05; p.rHandShape = "point";
  return p;
}

function buildUp(t) {
  const p = idle(t);
  const tc = TL.voice.command.start;
  const spread = smooth(18.4, 19.8, t);
  p.rHand = [p.px + 40, p.py - 1080]; p.rHandShape = "open";
  p.lHand = [p.px - 20, p.py - 1010];
  p.blink = 0.5 * (1 - smooth(tc - 0.1, tc + 0.2, t));
  p.look = [0, 0.5 * (1 - smooth(tc - 0.1, tc + 0.2, t))];
  p.smile = lerp(0.4, 0.05, smooth(tc, tc + 0.5, t)); p.brow = smooth(tc, tc + 0.4, t) * 0.9;
  p.neck = lerp(0.12, -0.02, smooth(tc - 0.2, tc + 0.6, t));
  if (spread > 0) {
    const q = P({ lSh: 1.35, rSh: 1.35, lEl: 0.25, rEl: 0.25, lFoot: [-100, 0], rFoot: [100, 0] });
    const f = Object.assign({}, p); delete f.rHand; delete f.lHand;
    for (const k of ["lSh", "rSh", "lEl", "rEl"]) f[k] = q[k];
    p._blend = { to: f, w: spread };
  }
  p.wings = smooth(18.6, 19.9, t);
  p.flare = 0.5 * smooth(18.6, 20, t); p.wind = 250 * sin(t * 3) * smooth(18.6, 20, t);
  p.py += -12 * smooth(18.6, 20, t);
  return p;
}

function powerA(B) { // 2 vuruşta bir kol savurma
  const k = Math.floor(B / 2) % 2 ? 1 : -1, ph = (B % 2) / 2;
  const hit = smooth(0, 0.18, ph) * (1 - smooth(0.6, 1, ph));
  const b = (1 - cos(TAU * B)) / 2;
  const p = P({ py: 28 * b + 10, px: 30 * k * hit, hip: 0.06 * k * hit, spine: -0.1 * k * hit, neck: 0.06 * k * hit,
                lFoot: [-125, 0], rFoot: [125, 0], smile: 0.35, brow: 0.6, wings: 1, wingFlap: 0.15 * hit });
  p[k < 0 ? "lSh" : "rSh"] = lerp(0.4, 1.58, hit); p[k < 0 ? "lEl" : "rEl"] = lerp(1.2, 0.0, hit);
  p[k < 0 ? "lHandShape" : "rHandShape"] = "open";
  const o = k < 0 ? "r" : "l";
  p[o + "Sh"] = 0.5; p[o + "El"] = 1.6; p[o + "HandShape"] = "fist";
  p.wind = 300 * k * hit;
  return p;
}

function crossOpen(B) {
  const ph = (B % 2) / 2;
  const open = smooth(0.0, 0.15, ph) * (1 - smooth(0.75, 1.0, ph));
  const b = (1 - cos(TAU * B)) / 2;
  const p = P({ py: 20 * b + 8, lFoot: [-115, 0], rFoot: [115, 0], smile: 0.5, brow: 0.4, wings: 1, wingFlap: 0.25 * open, flare: 0.3 * open, neck: -0.05 * open });
  const cy = p.py - 1110;
  const cl = [p.px + 60, cy], cr = [p.px - 60, cy];
  const ol = [p.px - 360, p.py - 1420], or = [p.px + 360, p.py - 1420];
  p.lHand = [lerp(cl[0], ol[0], open), lerp(cl[1], ol[1], open)];
  p.rHand = [lerp(cr[0], or[0], open), lerp(cr[1], or[1], open)];
  return p;
}

function hairSweep(B) {
  const u = (B % 4) / 4, a = PI * B / 2;
  const p = P({ px: 45 * sin(a), hip: -0.1 * sin(a), spine: 0.14 * sin(a), neck: -0.2 * sin(a + 0.6), py: 14 * (1 - cos(TAU * B)) / 2,
                lFoot: [-105, 0], rFoot: [105, 0], smile: 0.65, wings: 1, blink: 0.2, wind: 500 * sin(a + 0.6) });
  p.rSh = 0.3 + 2.6 * ease(clamp(u * 2, 0, 1)) * (1 - ease(clamp(u * 2 - 1, 0, 1)) * 0.6); p.rEl = 0.4;
  p.lHand = hipHand(p, -1);
  return p;
}

function finalPose(t) {
  const p = P({ px: 35, hip: -0.1, spine: 0.06, neck: -0.12, lFoot: [-80, 0], rFoot: [120, 0], smile: 0.6, brow: 0.3,
                wings: 1, flare: 0.25 + 0.05 * sin(t * 2), wind: 120 * sin(t * 2.4), py: 2 * sin(t * 2) });
  p.lHand = hipHand(p, -1);
  p.rSh = 1.75; p.rEl = 0.35; p.rWr = 0.4;
  return p;
}

function flustered(t) {
  const tf = TL.voice.flustered.start;
  const p = P({ py: 4 * sin(t * 13) * smooth(tf - 0.2, tf, t), spine: 0.03 * sin(t * 9), neck: 0.06 + 0.03 * sin(t * 7),
                lFoot: [-55, 0], rFoot: [55, 0], smile: 0, blush: smooth(tf - 0.4, tf + 0.3, t), pupil: 0.72, browUp: 1, brow: -0.6,
                wings: 1 - smooth(30.0, 30.9, t), look: [0, 0] });
  p.lSh = p.rSh = 0.32; p.lEl = p.rEl = 2.98;
  return p;
}

// zaman çizelgesi: [başlangıç, bitiş, fonksiyon]
const SEG = [
  [0, 7.6, (t) => intro(t)],
  [7.6, 10, (t, B) => stepTouch(B, t, "swing")],
  [10, 12, (t, B) => stepTouch(B, t, "wave")],
  [12, 13.9, (t, B) => clapUp(B)],
  [13.9, 15, (t, B) => spin(27.9, B)],
  [15, 16.2, (t, B) => pointPose(t, B)],
  [16.2, 20, (t) => buildUp(t)],
  [20, 22, (t, B) => powerA(B)],
  [22, 24, (t, B) => crossOpen(B)],
  [24, 26, (t, B) => hairSweep(B)],
  [26, 27.1, (t, B) => Object.assign(spin(52, B), { wings: 1, flare: 1 })],
  [27.1, 29.9, (t) => finalPose(t)],
  [29.9, 99, (t) => flustered(t)],
];

let charRef = null;
function resolveHands(p) {
  // İleri kinematik kolları el hedeflerine çevir (pozlar arası geçiş için)
  const r = charRef.rig(p);
  if (!p.lHand) p.lHand = r.arms.l.W.slice();
  if (!p.rHand) p.rHand = r.arms.r.W.slice();
  return p;
}
function mixPose(a, b, w) {
  if (w <= 0) return a; if (w >= 1) return b;
  a = resolveHands(Object.assign({}, a)); b = resolveHands(Object.assign({}, b));
  const o = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const x = a[k], y = b[k];
    if (typeof x === "number" && typeof y === "number") o[k] = lerp(x, y, w);
    else if (Array.isArray(x) && Array.isArray(y)) o[k] = x.map((v, i) => lerp(v, y[i], w));
    else o[k] = w < 0.5 ? (x ?? y) : (y ?? x);
  }
  return o;
}
function evalSeg(i, t) {
  const B = t / BEAT;
  let p = SEG[i][2](t, B);
  if (p._blend) { const bl = p._blend; delete p._blend; p = mixPose(p, bl.to, bl.w); }
  return p;
}
function poseAt(t) {
  let i = SEG.findIndex((s) => t >= s[0] && t < s[1]);
  if (i < 0) i = SEG.length - 1;
  let p = evalSeg(i, t);
  const X = 0.28;
  if (i > 0 && t < SEG[i][0] + X) p = mixPose(evalSeg(i - 1, t), p, ease((t - SEG[i][0]) / X));
  // göz kırpma
  const bt = (t + 0.7) % 3.9;
  p.blink = Math.max(p.blink || 0, bt < 0.14 ? sin(PI * bt / 0.14) : 0);
  // dudak senkronu
  const v = voiceAt(t);
  if (v) {
    p.mouth = clamp(v.amp * 1.5 - 0.08, 0, 1) * (0.75 + 0.25 * sin(t * 37));
    if (v.key === "command") p.smile = 0.05;
  }
  return p;
}

// ---- kamera ----------------------------------------------------------------
function camAt(t) {
  const full = { x: 0, y: -770, z: 1.0 };
  const close = { x: 0, y: -1180, z: 2.05 };
  let c;
  const mix = (a, b, w) => ({ x: lerp(a.x, b.x, w), y: lerp(a.y, b.y, w), z: lerp(a.z, b.z, w) });
  if (t < 8) c = mix({ x: 30, y: -1180, z: 1.75 - 0.015 * t }, full, ease((t - 6.4) / 1.6));
  else if (t < 16.2) c = full;
  else if (t < 20) c = mix(full, { x: 0, y: -1060, z: 1.45 }, ease((t - 16.2) / 3.4));
  else if (t < 28) c = mix({ x: 0, y: -840, z: 0.9 }, full, ease((t - 20) / 0.9));
  else if (t < 29.9) c = mix(full, { x: 40, y: -1000, z: 1.25 }, ease((t - 28) / 0.6));
  else c = mix({ x: 40, y: -1000, z: 1.25 }, { x: 0, y: -1290, z: 2.5 }, ease((t - 29.95) / 0.35));
  // vuruşta zoom nabzı ve sarsıntı
  const B = t / BEAT, ph = B % 1;
  let pulse = 0, shake = 0;
  if (t >= 8 && t < 16) pulse = 0.012 * Math.exp(-ph * 8);
  if (t >= 20 && t < 28) { pulse = 0.022 * Math.exp(-ph * 8); shake = 6 * Math.exp(-ph * 10); }
  shake += 26 * Math.exp(-Math.max(0, t - 20) * 4) * (t >= 20 ? 1 : 0) + 18 * Math.exp(-Math.max(0, t - 28) * 5) * (t >= 28 ? 1 : 0);
  c.z *= 1 + pulse;
  c.sx = shake * (hash(Math.floor(t * 30)) - 0.5); c.sy = shake * (hash(Math.floor(t * 30) + 99) - 0.5);
  return c;
}

// ---- sahne çizimi ----------------------------------------------------------
const power = (t) => smooth(18.4, 20.0, t) * (1 - smooth(30.0, 31.2, t));

function drawSky(ctx, t) {
  const pw = power(t);
  const g = ctx.createLinearGradient(0, 0, 0, H);
  const top = mixColor([18, 12, 46], [14, 0, 6], pw), mid = mixColor([70, 30, 100], [110, 8, 24], pw), low = mixColor([190, 90, 150], [240, 60, 40], pw);
  g.addColorStop(0, rgb(top)); g.addColorStop(0.55, rgb(mid)); g.addColorStop(0.8, rgb(low));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // yıldızlar
  for (let i = 0; i < 140; i++) {
    const x = hash(i) * W, y = hash(i + 500) * H * 0.6;
    const a = 0.3 + 0.7 * Math.abs(sin(t * (0.5 + hash(i + 9) * 2) + i));
    ctx.fillStyle = `rgba(255,${240 - pw * 120},${255 - pw * 160},${a * (1 - pw * 0.4)})`;
    ctx.fillRect(x, y, 2.2, 2.2);
  }
  // ay
  const mx = 820, my = 330;
  const mg = ctx.createRadialGradient(mx, my, 60, mx, my, 360);
  mg.addColorStop(0, `rgba(255,${230 - pw * 170},${230 - pw * 190},0.45)`); mg.addColorStop(1, "rgba(255,200,220,0)");
  ctx.fillStyle = mg; ctx.fillRect(0, 0, W, H);
  ctx.beginPath(); ctx.arc(mx, my, 110, 0, TAU);
  ctx.fillStyle = rgb(mixColor([255, 244, 236], [255, 70, 60], pw)); ctx.fill();
  ctx.fillStyle = "rgba(0,0,0,0.06)";
  for (const [x, y, r] of [[-30, -20, 26], [35, 30, 18], [10, -50, 12], [-40, 45, 14]]) { ctx.beginPath(); ctx.arc(mx + x, my + y, r, 0, TAU); ctx.fill(); }
}

function drawAcademy(ctx, t, cam) {
  // uzak gotik okul silüeti (hafif paralaks)
  const pw = power(t);
  const base = 1120 - (cam.y + 770) * 0.05 * cam.z;
  ctx.save(); ctx.translate(-cam.x * 0.05, 0);
  ctx.fillStyle = rgb(mixColor([30, 16, 48], [24, 2, 8], pw));
  ctx.beginPath(); ctx.moveTo(-50, base + 200);
  const bldg = [[-50, 900], [80, 900], [80, 820], [110, 760], [140, 820], [140, 880], [300, 880], [300, 700], [330, 620], [360, 700], [360, 860],
                [520, 860], [520, 560], [560, 470], [600, 560], [600, 860], [760, 860], [760, 720], [790, 650], [820, 720], [820, 880], [960, 880], [960, 800], [990, 740], [1020, 800], [1020, 900], [1130, 900]];
  for (const [x, y] of bldg) ctx.lineTo(x, base + (y - 900));
  ctx.lineTo(1130, base + 200); ctx.closePath(); ctx.fill();
  // pencereler
  for (let i = 0; i < 46; i++) {
    const x = 90 + (i % 23) * 40 + (i > 22 ? 20 : 0), y = base - 30 - (i > 22 ? 70 : 0) - (Math.abs(x - 560) < 40 ? 200 : 0);
    if (hash(i + 3) < 0.45) continue;
    const fl = 0.6 + 0.4 * sin(t * 2 + i);
    ctx.fillStyle = `rgba(255,${200 - pw * 150},${120 - pw * 100},${0.55 * fl})`;
    ctx.fillRect(x, y, 10, 16);
  }
  ctx.restore();
}

function drawFloor(ctx, t, toScreen) {
  const pw = power(t);
  const fy = toScreen(0, 0)[1];
  const hz = Math.min(fy - 400 * toScreen.z, 1320);
  const g = ctx.createLinearGradient(0, hz, 0, H);
  g.addColorStop(0, rgb(mixColor([40, 24, 60], [40, 4, 10], pw))); g.addColorStop(1, rgb(mixColor([8, 4, 16], [6, 0, 2], pw)));
  ctx.fillStyle = g; ctx.fillRect(0, hz, W, H - hz);
  ctx.strokeStyle = `rgba(255,255,255,0.05)`; ctx.lineWidth = 2;
  for (let i = -12; i <= 12; i++) { const a = toScreen(i * 160, -400), b = toScreen(i * 480, 600); ctx.beginPath(); ctx.moveTo(a[0], hz); ctx.lineTo(b[0], H); ctx.stroke(); }
}

function drawMagicCircle(ctx, t, toScreen, z) {
  const a = smooth(18.8, 20.2, t) * (1 - smooth(30.0, 31.0, t));
  if (a <= 0) return;
  const c = toScreen(0, 0);
  ctx.save(); ctx.translate(c[0], c[1] - 6); ctx.scale(z, z * 0.26);
  ctx.globalCompositeOperation = "lighter";
  const R = 460 * smooth(18.8, 19.8, t);
  const glow = ctx.createRadialGradient(0, 0, 0, 0, 0, R * 1.2);
  glow.addColorStop(0, `rgba(255,30,50,${0.35 * a})`); glow.addColorStop(1, "rgba(255,0,30,0)");
  ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(0, 0, R * 1.2, 0, TAU); ctx.fill();
  ctx.strokeStyle = `rgba(255,70,80,${0.9 * a})`; ctx.lineWidth = 6;
  for (const rr of [1, 0.86, 0.5]) { ctx.beginPath(); ctx.arc(0, 0, R * rr, 0, TAU); ctx.stroke(); }
  ctx.rotate(t * 0.6);
  ctx.lineWidth = 4;
  ctx.beginPath();
  for (let k = 0; k <= 6; k++) { const ang = k * TAU * 2 / 6 - PI / 2; const p = [cos(ang) * R * 0.86, sin(ang) * R * 0.86]; k ? ctx.lineTo(...p) : ctx.moveTo(...p); }
  ctx.stroke();
  ctx.beginPath();
  for (let k = 0; k <= 6; k++) { const ang = (k * TAU * 2 + PI * 2) / 6 - PI / 2 + PI / 6 * 0; const p = [cos(ang + PI / 3) * R * 0.86, sin(ang + PI / 3) * R * 0.86]; k ? ctx.lineTo(...p) : ctx.moveTo(...p); }
  ctx.stroke();
  // rünler
  ctx.rotate(-t * 1.2);
  for (let k = 0; k < 24; k++) {
    const ang = k * TAU / 24;
    ctx.save(); ctx.rotate(ang); ctx.translate(R * 0.93, 0);
    ctx.beginPath();
    const h = hash(k);
    ctx.moveTo(-12, -14); ctx.lineTo(h > 0.5 ? 12 : -4, 0); ctx.lineTo(-12, 14);
    if (h > 0.3) { ctx.moveTo(4, -14); ctx.lineTo(4, 14); }
    ctx.stroke(); ctx.restore();
  }
  ctx.restore();
}

function drawSpotlights(ctx, t) {
  const pw = power(t);
  const on = smooth(7.8, 8.2, t);
  if (on <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  const B = t / BEAT;
  const cols = pw > 0.5 ? [[255, 30, 40], [200, 0, 60]] : [[255, 80, 200], [80, 220, 255]];
  for (let i = 0; i < 4; i++) {
    const sx = 140 + i * 270, ang = 0.32 * sin(t * 1.1 + i * 1.7) + (i < 2 ? 0.2 : -0.2);
    const len = 2100;
    const ex = sx + Math.sin(ang) * len, ey = Math.cos(ang) * len;
    const c = cols[i % 2];
    const kick = (t > 8 && t < 16) || (t > 20 && t < 28) ? 0.6 + 0.4 * Math.exp(-(B % 1) * 5) : 0.6;
    const g = ctx.createLinearGradient(sx, 0, ex, ey);
    g.addColorStop(0, `rgba(${c},${0.32 * on * kick})`); g.addColorStop(1, `rgba(${c},0)`);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(sx - 10, -10);
    const px = Math.cos(ang) * 190, py = -Math.sin(ang) * 190;
    ctx.lineTo(ex + px, ey + py); ctx.lineTo(ex - px, ey - py); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

function drawAuraBack(ctx, t, anc, toScreen, z) {
  const a = power(t);
  if (a <= 0.001) return;
  const B = t / BEAT;
  const beat = (t > 20 && t < 28) ? Math.exp(-(B % 1) * 4) : 0;
  const ch = toScreen(...anc.chest);
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  const R = (720 + 80 * beat) * z;
  const g = ctx.createRadialGradient(ch[0], ch[1], 30 * z, ch[0], ch[1], R);
  g.addColorStop(0, `rgba(255,40,60,${0.5 * a})`); g.addColorStop(0.45, `rgba(170,0,30,${0.35 * a})`); g.addColorStop(1, "rgba(80,0,10,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
  // alev dilleri ve kara duman
  const hp = toScreen(...anc.hip);
  for (let i = 0; i < 90; i++) {
    const life = 1.2 + hash(i) * 0.8;
    const age = ((t + hash(i + 1) * 10) % life) / life;
    const ox = (hash(i + 2) - 0.5) * 520, oy = (hash(i + 3) - 0.3) * 900;
    const x = hp[0] + (ox + sin(t * 3 + i) * 30 * age) * z;
    const y = hp[1] + (oy + 200 - age * 800) * z;
    const r = (60 + 90 * hash(i + 4)) * (1 - age * 0.5) * z;
    const dark = i % 3 === 0;
    const gg = ctx.createRadialGradient(x, y, 0, x, y, r);
    if (dark) { gg.addColorStop(0, `rgba(10,0,4,${0.35 * a * sin(PI * age)})`); gg.addColorStop(1, "rgba(0,0,0,0)"); ctx.globalCompositeOperation = "source-over"; }
    else { gg.addColorStop(0, `rgba(255,${40 + 60 * hash(i + 5)},40,${0.28 * a * sin(PI * age)})`); gg.addColorStop(1, "rgba(120,0,10,0)"); ctx.globalCompositeOperation = "lighter"; }
    ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  ctx.globalCompositeOperation = "source-over";
}

function drawEmbers(ctx, t, anc, toScreen, z, amount) {
  if (amount <= 0.001) return;
  const hp = toScreen(...anc.hip);
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 70; i++) {
    const life = 1.5 + hash(i + 70) * 1.5;
    const age = ((t + hash(i + 71) * 10) % life) / life;
    const x = hp[0] + ((hash(i + 72) - 0.5) * 700 + sin(t * 2 + i) * 40) * z;
    const y = hp[1] + (300 - age * 1500 + hash(i + 73) * 200) * z;
    const r = (3 + 4 * hash(i + 74)) * z;
    ctx.fillStyle = `rgba(255,${120 + 100 * hash(i)},${80},${amount * sin(PI * age)})`;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  ctx.restore();
}

function drawLightning(ctx, t, anc, toScreen, z) {
  const a = power(t);
  if (a < 0.5 || t < 20 || t > 29.5) return;
  const B = t / BEAT, bar = Math.floor(B / 4), ph = (B % 4);
  if (ph > 0.35) return;
  const ch = toScreen(...anc.chest);
  ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.lineCap = "round";
  for (let k = 0; k < 3; k++) {
    let x = ch[0], y = ch[1];
    const dir = hash(bar * 7 + k) * TAU;
    ctx.beginPath(); ctx.moveTo(x, y);
    for (let s = 0; s < 9; s++) {
      x += cos(dir) * 70 * z + (hash(bar * 31 + k * 9 + s) - 0.5) * 80 * z;
      y += sin(dir) * 70 * z + (hash(bar * 17 + k * 5 + s) - 0.5) * 80 * z;
      ctx.lineTo(x, y);
    }
    const al = 1 - ph / 0.35;
    ctx.strokeStyle = `rgba(255,60,80,${0.5 * al})`; ctx.lineWidth = 12; ctx.stroke();
    ctx.strokeStyle = `rgba(255,220,220,${0.9 * al})`; ctx.lineWidth = 3; ctx.stroke();
  }
  ctx.restore();
}

function drawBokeh(ctx, t) {
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  const pw = power(t);
  for (let i = 0; i < 26; i++) {
    const x = (hash(i + 200) * W + t * (10 + 20 * hash(i + 201))) % W;
    const y = (hash(i + 202) * H - t * (15 + 25 * hash(i + 203)) + H * 10) % H;
    const r = 10 + 26 * hash(i + 204);
    ctx.fillStyle = pw > 0.5 ? `rgba(255,60,60,0.08)` : `rgba(${hash(i) > 0.5 ? "255,140,220" : "140,220,255"},0.08)`;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  ctx.restore();
}

// altyazılar
const SUBS = {
  warm: [["Oh my... you came all this way, just to watch me dance?", "Aman aman... Sırf beni dans ederken izlemek için onca yolu mu geldin?", 0.0],
         ["Then stay close. And don't you dare look away.", "O hâlde yakınımda kal. Ve sakın gözlerini kaçırmaya kalkma.", 0.56]],
  command: [["Enough playing. Now... witness the power of House Vermillion.", "Oyun bitti. Şimdi... Vermillion Hanesi'nin gücüne tanık ol.", 0]],
  flustered: [["W-wait! Were you recording this... the whole time?!", "D-dur! Bunu... baştan beri kaydediyor muydun?!", 0]],
};
function wrap(ctx, text, maxW) {
  const words = text.split(" "), lines = []; let cur = "";
  for (const w of words) { const tt = cur ? cur + " " + w : w; if (ctx.measureText(tt).width > maxW && cur) { lines.push(cur); cur = w; } else cur = tt; }
  if (cur) lines.push(cur); return lines;
}
function drawSubs(ctx, t) {
  for (const k of Object.keys(SUBS)) {
    const v = TL.voice[k];
    const list = SUBS[k];
    for (let i = 0; i < list.length; i++) {
      const s0 = v.start + list[i][2] * v.dur - 0.1;
      const s1 = i + 1 < list.length ? v.start + list[i + 1][2] * v.dur - 0.1 : v.start + v.dur + 0.5;
      if (t < s0 || t >= s1) continue;
      const a = env(t, s0, s1, 0.15, 0.2);
      ctx.save(); ctx.globalAlpha = a;
      ctx.font = "700 46px Nunito"; ctx.textAlign = "center";
      const tr = wrap(ctx, list[i][1], 900);
      ctx.font = "italic 600 30px Nunito";
      const en = wrap(ctx, list[i][0], 900);
      const hgt = tr.length * 58 + en.length * 40 + 40;
      const y0 = 1880 - hgt;
      ctx.fillStyle = "rgba(10,4,14,0.62)";
      roundRect(ctx, 60, y0, W - 120, hgt, 26); ctx.fill();
      let y = y0 + 52;
      ctx.fillStyle = "rgba(255,220,225,0.85)";
      for (const l of en) { ctx.fillText(l, W / 2, y - 6); y += 40; }
      ctx.font = "700 46px Nunito"; ctx.lineWidth = 6; ctx.strokeStyle = "rgba(60,0,10,0.9)"; ctx.fillStyle = "#fff";
      for (const l of tr) { ctx.strokeText(l, W / 2, y + 6); ctx.fillText(l, W / 2, y + 6); y += 58; }
      ctx.restore();
    }
  }
}
function drawNameCard(ctx, t) {
  const a = env(t, 1.6, 6.6, 0.6, 0.6);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a;
  const x = 70 + 30 * (1 - ease((t - 1.6) / 0.8)), y = 150;
  ctx.fillStyle = "rgba(20,4,10,0.55)"; roundRect(ctx, x - 20, y - 70, 720, 180, 20); ctx.fill();
  ctx.fillStyle = "#c8162e"; ctx.fillRect(x - 20, y - 70, 8, 180);
  ctx.font = "700 62px Cinzel"; ctx.fillStyle = "#fff"; ctx.fillText("Seraphine", x + 6, y);
  ctx.fillStyle = "#ff4a5a"; ctx.fillText("Vermillion", x + 6 + ctx.measureText("Seraphine ").width, y);
  ctx.font = "600 30px Nunito"; ctx.fillStyle = "rgba(255,230,235,0.92)";
  ctx.fillText("Vermillion Hanesi'nin Varisi", x + 8, y + 46);
  ctx.fillStyle = "rgba(170,240,230,0.92)"; ctx.fillText("Gizli Bilimler Kulübü Başkanı", x + 8, y + 86);
  ctx.restore();
}
function roundRect(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function mixColor(a, b, w) { return a.map((v, i) => Math.round(lerp(v, b[i], w))); }
function rgb(c) { return `rgb(${c[0]},${c[1]},${c[2]})`; }

// ---- ana döngü -------------------------------------------------------------
const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");
const off = document.createElement("canvas"); off.width = W; off.height = H;
const octx = off.getContext("2d");
const ch = new Character(); charRef = ch;
let simT = -1;
const DT = 1 / 30;

function advanceTo(t) {
  if (simT < 0 || t < simT - 1e-6) { ch.reset(); simT = -DT * 40; }
  while (simT + DT <= t + 1e-6) { simT += DT; ch.step(poseAt(Math.max(0, simT)), DT); }
}

window.renderFrame = function (t) {
  advanceTo(t);
  const pose = poseAt(t);
  const cam = camAt(t);
  const S = cam.z;
  const toScreen = (x, y) => [W / 2 + (x - cam.x) * S + cam.sx, H / 2 + (y - cam.y) * S + cam.sy];
  toScreen.z = S;
  const anc = ch.anchors(pose);

  drawSky(ctx, t);
  drawAcademy(ctx, t, cam);
  drawSpotlights(ctx, t);
  drawFloor(ctx, t, toScreen);
  drawMagicCircle(ctx, t, toScreen, S);
  drawBokeh(ctx, t);
  drawAuraBack(ctx, t, anc, toScreen, S);

  // karakter (ayrı katman: parıltı + yansıma)
  octx.setTransform(1, 0, 0, 1, 0, 0); octx.clearRect(0, 0, W, H);
  const o = toScreen(0, 0);
  octx.setTransform(S * pose.flipX, 0, 0, S, o[0], o[1]);
  ch.draw(octx, pose);
  const fy = o[1];
  // yansıma
  ctx.save(); ctx.globalAlpha = 0.22;
  ctx.translate(0, fy * 2); ctx.scale(1, -1); ctx.drawImage(off, 0, 0);
  ctx.restore();
  const fade = ctx.createLinearGradient(0, fy, 0, Math.min(H, fy + 500));
  const pw = power(t);
  fade.addColorStop(0, "rgba(0,0,0,0)"); fade.addColorStop(1, rgb(mixColor([8, 4, 16], [6, 0, 2], pw)));
  ctx.fillStyle = fade; ctx.fillRect(0, fy, W, H - fy);
  // parıltı
  const pwr = power(t);
  ctx.save();
  if (pwr > 0.01) { ctx.shadowColor = `rgba(255,20,50,${0.85 * pwr})`; ctx.shadowBlur = 50; }
  else { ctx.shadowColor = "rgba(255,180,230,0.35)"; ctx.shadowBlur = 24; }
  ctx.drawImage(off, 0, 0);
  ctx.restore();

  drawLightning(ctx, t, anc, toScreen, S);
  drawEmbers(ctx, t, anc, toScreen, S, power(t));

  // ışık patlaması
  const flash = Math.exp(-Math.max(0, t - 20) * 5) * (t >= 20 ? 1 : 0) + Math.exp(-Math.max(0, t - 28) * 6) * (t >= 28 ? 0.6 : 0);
  if (flash > 0.01) { ctx.fillStyle = `rgba(255,${200 - 120 * Math.min(1, t - 20 > 0 ? 1 : 0)},${190},${flash})`; ctx.fillRect(0, 0, W, H); }
  // vinyet
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75);
  vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,0.5)");
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);

  drawNameCard(ctx, t);
  drawSubs(ctx, t);
  // giriş/çıkış kararması
  const black = 1 - smooth(0, 0.8, t) + smooth(TOTAL - 0.9, TOTAL, t);
  if (black > 0.001) { ctx.fillStyle = `rgba(0,0,0,${clamp(black, 0, 1)})`; ctx.fillRect(0, 0, W, H); }
};

// karakter tasarım sayfası için tekil poz çizimi
window.renderPortrait = function (mode) {
  const t = mode === "power" ? 24.6 : 5.0;
  renderFrame(t);
};
window.TOTAL = TOTAL;
})();
