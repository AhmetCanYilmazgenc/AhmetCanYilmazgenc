// Seraphine Vermillion — tamamen kodla (Canvas 2D) çizilen anime karakteri.
// Gövde koordinatları: zemin y=0, yukarı negatif; boy ≈ 1500 birim (172 cm).
"use strict";

const TAU = Math.PI * 2;
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
function smooth(e0, e1, x) { const t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); }

// ---- 2B afin matrisler [a,b,c,d,e,f] (canvas düzeni) -----------------------
const M = {
  I: () => [1, 0, 0, 1, 0, 0],
  T: (x, y) => [1, 0, 0, 1, x, y],
  R: (a) => { const c = Math.cos(a), s = Math.sin(a); return [c, s, -s, c, 0, 0]; },
  S: (x, y) => [x, 0, 0, y, 0, 0],
  mul(m, n) {
    return [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
            m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
            m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
  },
  chain(...ms) { return ms.reduce((a, b) => M.mul(a, b)); },
  about(cx, cy, a) { return M.chain(M.T(cx, cy), M.R(a), M.T(-cx, -cy)); },
  ap(m, x, y) { return [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]]; },
};

// Catmull-Rom üzerinden yumuşak yol
function smoothPath(ctx, pts, closed, k = 0.5) {
  const n = pts.length;
  if (n < 2) return;
  const P = (i) => closed ? pts[(i + n) % n] : pts[clamp(i, 0, n - 1)];
  ctx.moveTo(pts[0][0], pts[0][1]);
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k / 3, p1[1] + (p2[1] - p0[1]) * k / 3,
                      p2[0] - (p3[0] - p1[0]) * k / 3, p2[1] - (p3[1] - p1[1]) * k / 3,
                      p2[0], p2[1]);
  }
  if (closed) ctx.closePath();
}

// Kalınlığı değişen uzuv/şerit dış hattı
function ribbon(pts, radii, capStart = true, capEnd = true) {
  const L = [], Rr = [];
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
    const r = radii[i];
    L.push([pts[i][0] - dy * r, pts[i][1] + dx * r]);
    Rr.push([pts[i][0] + dy * r, pts[i][1] - dx * r]);
  }
  const dir = (i, j) => { const dx = pts[j][0] - pts[i][0], dy = pts[j][1] - pts[i][1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; };
  const out = [];
  if (capStart) { const d = dir(1, 0); out.push([pts[0][0] + d[0] * radii[0] * 0.75, pts[0][1] + d[1] * radii[0] * 0.75]); }
  out.push(...L);
  if (capEnd) { const d = dir(n - 2, n - 1); out.push([pts[n - 1][0] + d[0] * radii[n - 1] * 0.75, pts[n - 1][1] + d[1] * radii[n - 1] * 0.75]); }
  for (let i = n - 1; i >= 0; i--) out.push(Rr[i]);
  return out;
}

function fillPath(ctx, pts, fill, stroke, lw = 2, k = 0.5) {
  ctx.beginPath(); smoothPath(ctx, pts, true, k);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.lineJoin = "round"; ctx.stroke(); }
}

// ---- Renkler ---------------------------------------------------------------
const C = {
  skin: "#fde9df", skinSh: "#f2c7bb", skinLine: "#c98579", blush: "rgba(255,110,130,",
  hair: "#c8162e", hairL: "#ec3a4c", hairD: "#7d0918", hairHi: "#ff8a88", hairLine: "#45040e",
  shirt: "#fbfbff", shirtSh: "#d9d9ea", line: "#2a1420",
  corset: "#6c1426", corsetL: "#8f2236", corsetD: "#3e0712",
  blazer: "#17141d", blazerL: "#3b3550", blazerD: "#07060a",
  skirt: "#c4202e", skirtD: "#8c1220", skirtL: "#e2414c",
  sock: "#121016", sockL: "#3a3444", shoe: "#6e3a1d", shoeL: "#9a5a30", shoeD: "#3a1c0c",
  ribbon: "#d61a30", gold: "#d9b25a",
  irisD: "#0a4d55", iris: "#15b3aa", irisL: "#7af2dd", pupil: "#06303a",
};

// ---- Saç teli (Verlet) -----------------------------------------------------
class Strand {
  constructor(root, n, seg, restFn, width, shade) {
    this.root = root; this.n = n; this.seg = seg; this.restFn = restFn;
    this.width = width; this.shade = shade; this.p = null;
  }
  reset(headM, flare) {
    this.p = [];
    for (let i = 0; i < this.n; i++) {
      const q = this.rest(headM, i, flare);
      this.p.push({ x: q[0], y: q[1], px: q[0], py: q[1] });
    }
  }
  rest(headM, i, flare) {
    const r = M.ap(headM, this.root[0], this.root[1]);
    const o = this.restFn(i * this.seg, flare);
    return [r[0] + o[0], r[1] + o[1]];
  }
  step(headM, dt, flare, wind) {
    if (!this.p) this.reset(headM, flare);
    const g = 1400 * dt * dt;
    for (let i = 1; i < this.n; i++) {
      const p = this.p[i];
      const vx = (p.x - p.px) * 0.93, vy = (p.y - p.py) * 0.93;
      p.px = p.x; p.py = p.y;
      const q = this.rest(headM, i, flare);
      const k = 0.06 + 0.10 * (1 - i / this.n);
      p.x += vx + (q[0] - p.x) * k + wind * dt * dt * (i / this.n);
      p.y += vy + g * 0.15 + (q[1] - p.y) * k;
    }
    const r0 = this.rest(headM, 0, flare);
    this.p[0].x = this.p[0].px = r0[0]; this.p[0].y = this.p[0].py = r0[1];
    for (let it = 0; it < 4; it++) {
      for (let i = 1; i < this.n; i++) {
        const a = this.p[i - 1], b = this.p[i];
        const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
        const f = (d - this.seg) / d;
        if (i === 1) { b.x -= dx * f; b.y -= dy * f; }
        else { a.x += dx * f * 0.5; a.y += dy * f * 0.5; b.x -= dx * f * 0.5; b.y -= dy * f * 0.5; }
      }
    }
  }
  draw(ctx) {
    const pts = this.p.map((p) => [p.x, p.y]);
    const radii = pts.map((_, i) => {
      const t = i / (this.n - 1);
      const root = this.thinRoot ? smooth(0, 0.25, t) * 0.8 + 0.2 : smooth(0, 0.2, t) * 0.5 + 0.5;
      return root * this.width * (0.75 + 0.35 * Math.sin(Math.PI * Math.min(1, t * 1.6))) * (1 - t * t * 0.93);
    });
    const shape = ribbon(pts, radii, false, true);
    const g = ctx.createLinearGradient(pts[0][0], pts[0][1], pts[pts.length - 1][0], pts[pts.length - 1][1]);
    const s = this.shade;
    g.addColorStop(0, s ? C.hairD : "#a3101f");
    g.addColorStop(0.35, s ? C.hair : C.hairL);
    g.addColorStop(1, s ? C.hairD : C.hair);
    fillPath(ctx, shape, g, C.hairLine, 1.6);
    // parlak şerit
    ctx.beginPath();
    smoothPath(ctx, pts.slice(1, Math.floor(this.n * 0.7)).map((p, i) => [p[0] + radii[i + 1] * 0.25, p[1]]), false);
    ctx.strokeStyle = s ? "rgba(255,120,120,0.25)" : "rgba(255,150,150,0.45)";
    ctx.lineWidth = 2.2; ctx.stroke();
  }
}

// ---- Karakter --------------------------------------------------------------
class Character {
  constructor() {
    this.strands = null; this.locks = null; this.ahoge = { a: 0, v: 0 };
    this.skirt = { x: 0, v: 0, flare: 0 }; this.prevHead = null; this.t = 0;
  }

  // Kemik zinciri: pozdan dönüşüm matrisleri
  rig(p) {
    const P = M.chain(M.T(p.px || 0, p.py || 0), M.about(0, -830, p.hip || 0));
    const Cm = M.mul(P, M.about(0, -960, p.spine || 0));
    const H = M.chain(Cm, M.about(0, -1250, p.neck || 0), M.T(p.headX || 0, 0));
    const Hd = M.mul(H, M.T(0, -1370));
    const bodyA = (p.hip || 0) + (p.spine || 0);
    const r = { P, C: Cm, H: Hd, bodyA, headA: bodyA + (p.neck || 0) };
    r.torso = (x, y) => {
      const w = smooth(-905, -1060, y);
      const a = M.ap(P, x, y), b = M.ap(Cm, x, y);
      return [lerp(a[0], b[0], w), lerp(a[1], b[1], w)];
    };
    // kollar
    r.arms = {};
    for (const s of [-1, 1]) {
      const key = s < 0 ? "l" : "r";
      const S = M.ap(Cm, s * 112, -1212);
      const L1 = 250, L2 = 228;
      let E, W;
      const tgt = p[key + "Hand"];
      if (tgt) {
        [E, W] = ik2(S, tgt, L1, L2, s, 1, p.elbowDown);
      } else {
        const a = p[key + "Sh"] ?? 0.12, e = p[key + "El"] ?? 0.05;
        const t1 = -s * a + bodyA, t2 = -s * (a + e) + bodyA;
        E = [S[0] - Math.sin(t1) * L1, S[1] + Math.cos(t1) * L1];
        W = [E[0] - Math.sin(t2) * L2, E[1] + Math.cos(t2) * L2];
      }
      const handA = Math.atan2(W[1] - E[1], W[0] - E[0]) + (p[key + "Wr"] || 0) * -s;
      r.arms[key] = { S, E, W, s, handA, hand: p[key + "HandShape"] || "open" };
    }
    // bacaklar (IK)
    r.legs = {};
    for (const s of [-1, 1]) {
      const key = s < 0 ? "l" : "r";
      const Hj = M.ap(P, s * 62, -800);
      const f = p[key + "Foot"] || [s * 72, 0];
      const lift = p[key + "Lift"] || 0;
      const A = [f[0], f[1] - 48 - lift];
      const [K] = ik2(Hj, A, 395, 385, s, 0.55);
      r.legs[key] = { Hj, K, A, s, lift };
    }
    return r;
  }

  reset() { this.strands = null; this.locks = null; this.prevHead = null; this.ahoge = { a: 0, v: 0 }; this.skirt = { x: 0, v: 0, flare: 0 }; }

  initHair() {
    const W = (d) => d < 150 ? lerp(92, 150, d / 150) : d < 320 ? lerp(150, 168, (d - 150) / 170) : lerp(168, 140, clamp((d - 320) / 420, 0, 1));
    this.strands = [];
    const N = 15;
    for (let j = 0; j < N; j++) {
      const u = j / (N - 1) * 2 - 1;           // -1..1
      const x0 = u * 92, y0 = -20 + Math.abs(u) * 30;
      const len = 600 + 130 * Math.abs(u) + (j % 3) * 18;
      const n = 12, seg = len / (n - 1);
      const restFn = (d, flare) => {
        const w = W(d) * (1 + flare * clamp(d / 400, 0, 1.2));
        return [u * w - x0 + Math.sin(d / 140 + u * 3) * 6, d * 0.985];
      };
      this.strands.push(new Strand([x0, y0], n, seg, restFn, 46 - Math.abs(u) * 8, j % 2));
    }
    // ön perçem tutamları (yüzü çevreleyen uzun teller)
    this.locks = [];
    for (const s of [-1, 1]) {
      for (const [rx, ry, len, wd, out] of [[76, 60, 330, 15, 0.12], [88, 50, 430, 17, 0.24]]) {
        const n = 9, seg = len / (n - 1);
        const restFn = (d, flare) => [s * (d * out + Math.sin(d / 90) * 5) * (1 + flare * 0.6), d];
        const st = new Strand([s * rx, ry], n, seg, restFn, wd, 0); st.thinRoot = true; this.locks.push(st);
      }
    }
  }

  // fizik adımı
  step(pose, dt) {
    const r = this.rig(pose);
    if (!this.strands) this.initHair();
    const flare = pose.flare || 0;
    const sub = 3;
    for (let k = 0; k < sub; k++) {
      for (const s of this.strands) s.step(r.H, dt / sub, flare, pose.wind || 0);
      for (const s of this.locks) s.step(r.H, dt / sub, flare, pose.wind || 0);
    }
    const hp = M.ap(r.H, 0, 0);
    if (this.prevHead && dt > 0) {
      const vx = (hp[0] - this.prevHead[0]) / dt, vy = (hp[1] - this.prevHead[1]) / dt;
      this.ahoge.v += (-this.ahoge.a * 160 - this.ahoge.v * 7 - vx * 0.004 + vy * 0.002) * dt;
      this.ahoge.a = clamp(this.ahoge.a + this.ahoge.v * dt, -0.7, 0.7);
      const sx = (pose.px || 0);
      this.skirt.v += ((sx - this.skirt.x) * 90 - this.skirt.v * 9) * dt;
      this.skirt.x += this.skirt.v * dt;
    }
    this.prevHead = hp;
    this.t += dt;
  }

  // ---- ÇİZİM ---------------------------------------------------------------
  draw(ctx, pose) {
    const r = this.rig(pose);
    if (!this.strands) { this.initHair(); for (const s of this.strands) s.reset(r.H, 0); for (const s of this.locks) s.reset(r.H, 0); }
    if (pose.wings > 0.01) this.drawWings(ctx, r, pose);
    this.drawHairMass(ctx);
    for (const s of this.strands) s.draw(ctx);
    this.drawLegs(ctx, r);
    this.drawTorso(ctx, r, pose);
    this.drawSkirt(ctx, r, pose);
    this.drawNeck(ctx, r);
    this.drawHead(ctx, r, pose);
    for (const s of this.locks) s.draw(ctx);
    this.drawArm(ctx, r.arms.l);
    this.drawArm(ctx, r.arms.r);
  }

  drawHairMass(ctx) {
    const L = this.strands[0].p, R = this.strands[this.strands.length - 1].p;
    const n = Math.min(L.length, R.length) - 1;
    const pts = [];
    for (let i = 0; i <= n - 2; i++) pts.push([L[i].x - 14, L[i].y]);
    const mid = this.strands[this.strands.length >> 1].p;
    pts.push([mid[n - 1].x, mid[n - 1].y]);
    for (let i = n - 2; i >= 0; i--) pts.push([R[i].x + 14, R[i].y]);
    const g = ctx.createLinearGradient(0, pts[0][1], 0, mid[n - 1].y);
    g.addColorStop(0, "#5c0612"); g.addColorStop(1, "#8a0c1c");
    fillPath(ctx, pts, g, null);
  }

  drawLegs(ctx, r) {
    for (const key of ["l", "r"]) {
      const { Hj, K, A, s } = r.legs[key];
      const at = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
      const top = [Hj[0] + s * 4, Hj[1] - 30];
      const pts = [top, at(Hj, K, 0.45), K, at(K, A, 0.3), at(K, A, 0.75), A];
      const rad = [64, 52, 35, 39, 26, 21];
      const shape = ribbon(pts, rad, false, false);
      const g = ctx.createLinearGradient(Hj[0] - 60, 0, Hj[0] + 60, 0);
      g.addColorStop(0, s < 0 ? C.skinSh : C.skin); g.addColorStop(0.5, C.skin); g.addColorStop(1, s < 0 ? C.skin : C.skinSh);
      fillPath(ctx, shape, g, C.skinLine, 1.8);
      // diz üstü çorap
      const st = at(Hj, K, 0.58);
      const spts = [st, at(st, K, 0.5), K, at(K, A, 0.3), at(K, A, 0.75), A];
      const srad = [47.5, 42, 36.5, 40.5, 27.5, 22.5];
      const sshape = ribbon(spts, srad, false, false);
      const sg = ctx.createLinearGradient(K[0] - 45, 0, K[0] + 45, 0);
      sg.addColorStop(0, C.sock); sg.addColorStop(0.45 + s * 0.08, C.sockL); sg.addColorStop(1, C.sock);
      fillPath(ctx, sshape, sg, "#000", 1.8);
      // çorap bandı
      const n = norm(K[0] - st[0], K[1] - st[1]);
      ctx.beginPath();
      ctx.moveTo(st[0] + n[1] * 48, st[1] - n[0] * 48);
      ctx.lineTo(st[0] - n[1] * 48, st[1] + n[0] * 48);
      ctx.strokeStyle = "#060508"; ctx.lineWidth = 11; ctx.stroke();
      ctx.strokeStyle = "rgba(120,110,140,0.5)"; ctx.lineWidth = 1.5; ctx.stroke();
      // ayakkabı
      this.drawShoe(ctx, A, s);
    }
  }

  drawShoe(ctx, A, s) {
    ctx.save(); ctx.translate(A[0] + s * 6, A[1] + 26); ctx.rotate(s * 0.12); ctx.scale(1.25, 1.2);
    ctx.beginPath();
    ctx.moveTo(-26, -16); ctx.bezierCurveTo(-34, 0, -32, 22, -10, 25); ctx.lineTo(10, 25);
    ctx.bezierCurveTo(32, 22, 34, 0, 26, -16); ctx.bezierCurveTo(12, -10, -12, -10, -26, -16); ctx.closePath();
    const g = ctx.createLinearGradient(0, -16, 0, 26);
    g.addColorStop(0, C.shoeL); g.addColorStop(0.6, C.shoe); g.addColorStop(1, C.shoeD);
    ctx.fillStyle = g; ctx.fill(); ctx.strokeStyle = "#2a1206"; ctx.lineWidth = 1.8; ctx.stroke();
    ctx.fillStyle = "#2a1206"; ctx.fillRect(-27, 22, 54, 6);                       // taban
    ctx.beginPath(); ctx.moveTo(-24, -4); ctx.quadraticCurveTo(0, 4, 24, -4);           // makosen kayışı
    ctx.strokeStyle = C.shoeD; ctx.lineWidth = 5; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(-8, 9, 6, 3, -0.2, 0, TAU); ctx.fillStyle = "rgba(255,220,180,0.35)"; ctx.fill();
    ctx.restore();
  }

  torsoOutline(r, yTop, yBot, widen = 0) {
    const prof = [[-1245, 37], [-1222, 92], [-1205, 116], [-1150, 108], [-1110, 113], [-1080, 110], [-1045, 92],
                  [-1000, 82], [-960, 78], [-910, 92], [-870, 110], [-820, 124], [-790, 122]];
    const w = (y) => {
      for (let i = 0; i < prof.length - 1; i++) {
        const [y0, w0] = prof[i], [y1, w1] = prof[i + 1];
        if (y <= y0 && y >= y1 || y >= y0 && y <= y1) return lerp(w0, w1, (y - y0) / (y1 - y0));
      }
      return y > -790 ? 122 : 37;
    };
    const L = [], R = [];
    const n = 16;
    for (let i = 0; i <= n; i++) {
      const y = lerp(yTop, yBot, i / n);
      L.push(r.torso(-w(y) - widen, y)); R.push(r.torso(w(y) + widen, y));
    }
    return { L, R, w, pts: [...L, ...R.reverse()] };
  }

  drawTorso(ctx, r, pose) {
    const T = r.torso;
    // gömlek
    const o = this.torsoOutline(r, -1240, -860);
    const g = ctx.createLinearGradient(T(-110, 0)[0], 0, T(110, 0)[0], 0);
    g.addColorStop(0, C.shirtSh); g.addColorStop(0.35, C.shirt); g.addColorStop(1, C.shirtSh);
    fillPath(ctx, o.pts, g, C.line, 2, 0.3);
    // göğüs gölgesi (yumuşak)
    ctx.strokeStyle = "rgba(150,140,175,0.55)"; ctx.lineWidth = 2;
    for (const s of [-1, 1]) {
      ctx.beginPath();
      const a = T(s * 98, -1090), b = T(s * 62, -1055), c = T(s * 18, -1068);
      ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(b[0], b[1], c[0], c[1]); ctx.stroke();
    }
    // korse yelek
    const cp = [];
    for (let i = 0; i <= 10; i++) { const u = i / 10 * 2 - 1; const y = -1062 + Math.abs(Math.sin(u * Math.PI)) * 10 - (1 - Math.abs(u)) * 4; cp.push(T(u * (o.w(y) - 2), y)); }
    const cb = [];
    for (let i = 10; i >= 0; i--) { const u = i / 10 * 2 - 1; const y = -872 + (1 - u * u) * 26; cb.push(T(u * (o.w(y) + 1), y)); }
    const cg = ctx.createLinearGradient(T(-100, 0)[0], 0, T(100, 0)[0], 0);
    cg.addColorStop(0, C.corsetD); cg.addColorStop(0.4, C.corsetL); cg.addColorStop(0.6, C.corset); cg.addColorStop(1, C.corsetD);
    ctx.beginPath(); ctx.moveTo(...cp[0]); for (const p of cp.slice(1)) ctx.lineTo(...p); for (const p of cb) ctx.lineTo(...p); ctx.closePath();
    ctx.fillStyle = cg; ctx.fill(); ctx.strokeStyle = "#250309"; ctx.lineWidth = 2; ctx.stroke();
    // korse dikişleri ve bağcıklar
    ctx.strokeStyle = "rgba(20,0,5,0.55)"; ctx.lineWidth = 1.5;
    for (const sx of [-50, 50]) { ctx.beginPath(); const a = T(sx, -1052), b = T(sx * 0.9, -960), c = T(sx * 1.05, -872); ctx.moveTo(...a); ctx.quadraticCurveTo(...b, ...c); ctx.stroke(); }
    ctx.strokeStyle = C.gold; ctx.lineWidth = 2;
    for (let y = -1040; y < -880; y += 22) {
      const a = T(-9, y), b = T(9, y + 16), c = T(9, y), d = T(-9, y + 16);
      ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.moveTo(...c); ctx.lineTo(...d); ctx.stroke();
    }
    for (let y = -1040; y < -870; y += 22) for (const sx of [-9, 9]) { const p = T(sx, y); ctx.beginPath(); ctx.arc(p[0], p[1], 2.4, 0, TAU); ctx.fillStyle = C.gold; ctx.fill(); }
    // yaka
    for (const s of [-1, 1]) {
      const a = T(s * 4, -1232), b = T(s * 46, -1250), c = T(s * 40, -1212);
      ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.closePath();
      ctx.fillStyle = C.shirt; ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1.8; ctx.stroke();
    }
    // ceket panelleri
    for (const s of [-1, 1]) {
      const pts = [T(s * 42, -1248), T(s * 96, -1226), T(s * 120, -1205)];
      for (let y = -1170; y <= -830; y += 40) pts.push(T(s * (o.w(y) + 5), y));
      pts.push(T(s * 128, -818)); pts.push(T(s * 84, -826));
      pts.push(T(s * 74, -900)); pts.push(T(s * 84, -1000)); pts.push(T(s * 102, -1070)); pts.push(T(s * 84, -1125));
      pts.push(T(s * 62, -1150)); pts.push(T(s * 40, -1205));
      const bg = ctx.createLinearGradient(T(s * 125, 0)[0], 0, T(s * 70, 0)[0], 0);
      bg.addColorStop(0, C.blazerD); bg.addColorStop(0.7, C.blazer); bg.addColorStop(1, C.blazerL);
      ctx.beginPath(); ctx.moveTo(...pts[0]); for (const p of pts.slice(1)) ctx.lineTo(...p); ctx.closePath();
      ctx.fillStyle = bg; ctx.fill(); ctx.strokeStyle = "#000"; ctx.lineWidth = 2; ctx.stroke();
      // klapa
      const lp = [T(s * 42, -1248), T(s * 62, -1150), T(s * 84, -1125), T(s * 98, -1145), T(s * 82, -1180), T(s * 70, -1240)];
      ctx.beginPath(); ctx.moveTo(...lp[0]); for (const p of lp.slice(1)) ctx.lineTo(...p); ctx.closePath();
      ctx.fillStyle = "#24202c"; ctx.fill(); ctx.strokeStyle = "rgba(140,130,170,0.55)"; ctx.lineWidth = 1.5; ctx.stroke();
      // kenar parlaması ve düğme
      ctx.beginPath(); const e1 = T(s * 84, -1125), e2 = T(s * 102, -1070), e3 = T(s * 84, -1000), e4 = T(s * 74, -900);
      ctx.moveTo(...e1); ctx.lineTo(...e2); ctx.lineTo(...e3); ctx.lineTo(...e4);
      ctx.strokeStyle = "rgba(170,160,210,0.45)"; ctx.lineWidth = 2; ctx.stroke();
      const bt = T(s * 82, -935); ctx.beginPath(); ctx.arc(bt[0], bt[1], 5, 0, TAU); ctx.fillStyle = C.gold; ctx.fill();
    }
    // arma (sol göğüs cebinde)
    const em = T(-104, -1010);
    ctx.save(); ctx.translate(...em); ctx.rotate(r.bodyA);
    ctx.beginPath(); ctx.moveTo(0, -9); ctx.lineTo(7, -4); ctx.lineTo(6, 6); ctx.lineTo(0, 10); ctx.lineTo(-6, 6); ctx.lineTo(-7, -4); ctx.closePath();
    ctx.fillStyle = C.gold; ctx.fill(); ctx.restore();
    // kurdele
    const rb = T(0, -1228);
    ctx.save(); ctx.translate(...rb); ctx.rotate(r.bodyA);
    ctx.fillStyle = C.ribbon; ctx.strokeStyle = "#5a0610"; ctx.lineWidth = 1.6;
    for (const s of [-1, 1]) {
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(s * 18, -18, s * 34, -10, s * 30, 4); ctx.bezierCurveTo(s * 26, 14, s * 12, 8, 0, 0); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(s * 2, 2); ctx.lineTo(s * 14, 44); ctx.lineTo(s * 8, 40); ctx.lineTo(s * 4, 46); ctx.lineTo(-s * 1, 4); ctx.closePath(); ctx.fill(); ctx.stroke();
    }
    ctx.beginPath(); ctx.ellipse(0, 1, 6, 7, 0, 0, TAU); ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  drawSkirt(ctx, r, pose) {
    const P = r.P;
    const flare = pose.flare || 0;
    const sw = clamp((this.skirt.x - (pose.px || 0)) * 0.6, -60, 60);
    const N = 14;
    const top = [], hem = [];
    for (let i = 0; i <= N; i++) {
      const u = i / N * 2 - 1;
      top.push(M.ap(P, u * 104, -902 + (1 - u * u) * 6));
      const hw = 176 + flare * 70;
      const hy = -688 - flare * 50 * (u * u) + (i % 2 ? 6 : 0);
      const hx = u * hw + sw * (0.6 + 0.4 * Math.abs(u));
      hem.push(M.ap(P, hx, hy + Math.sin(u * 2.5 + this.t * 3) * flare * 10));
    }
    // dış şekil
    ctx.beginPath(); ctx.moveTo(...top[0]);
    for (const p of top.slice(1)) ctx.lineTo(...p);
    ctx.lineTo(...hem[N]);
    for (let i = N - 1; i >= 0; i--) { const a = hem[i + 1], b = hem[i]; ctx.quadraticCurveTo((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 9, b[0], b[1]); }
    ctx.closePath();
    ctx.fillStyle = C.skirt; ctx.fill(); ctx.strokeStyle = "#4e0610"; ctx.lineWidth = 2.2; ctx.stroke();
    // pliler
    for (let i = 0; i < N; i++) {
      const a = top[i], b = top[i + 1], c = hem[i + 1], d = hem[i];
      if (i % 2 === 0) {
        ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.lineTo(...d); ctx.closePath();
        ctx.fillStyle = "rgba(90,0,12,0.28)"; ctx.fill();
      }
      ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...d); ctx.strokeStyle = "rgba(70,0,10,0.6)"; ctx.lineWidth = 1.4; ctx.stroke();
    }
    // beyaz şerit
    ctx.beginPath();
    for (let i = 0; i <= N; i++) { const a = M.ap(P, 0, 0); const t = top[i], h = hem[i]; const p = [lerp(t[0], h[0], 0.86), lerp(t[1], h[1], 0.86)]; i ? ctx.lineTo(...p) : ctx.moveTo(...p); }
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 7; ctx.stroke();
    // kemer
    ctx.beginPath(); ctx.moveTo(...top[0]); for (const p of top.slice(1)) ctx.lineTo(...p);
    ctx.strokeStyle = C.skirtD; ctx.lineWidth = 10; ctx.stroke();
  }

  drawNeck(ctx, r) {
    const T = (x, y) => M.ap(r.C, x, y);
    const H = (x, y) => M.ap(r.H, x, y);
    const pts = [T(-30, -1238), H(-27, 60), H(27, 60), T(30, -1238)];
    ctx.beginPath(); ctx.moveTo(...pts[0]); ctx.lineTo(...pts[1]); ctx.lineTo(...pts[2]); ctx.lineTo(...pts[3]); ctx.closePath();
    ctx.fillStyle = C.skin; ctx.fill(); ctx.strokeStyle = C.skinLine; ctx.lineWidth = 1.6; ctx.stroke();
    ctx.beginPath(); const a = H(-27, 70), b = H(0, 120), c = H(27, 70); ctx.moveTo(...a); ctx.quadraticCurveTo(...b, ...c); ctx.closePath();
    ctx.fillStyle = C.skinSh; ctx.fill();
  }

  drawHead(ctx, r, pose) {
    ctx.save();
    const o = M.ap(r.H, 0, 0);
    ctx.translate(o[0], o[1]); ctx.rotate(r.headA);
    const turn = pose.turn || 0, fx = turn * 10;
    // arka kafa saçı
    ctx.beginPath(); ctx.ellipse(0, -20, 108, 112, 0, 0, TAU);
    ctx.fillStyle = C.hairD; ctx.fill();
    // yüz
    ctx.beginPath();
    ctx.moveTo(-86 + fx * 0.4, -50);
    ctx.bezierCurveTo(-90 + fx * 0.3, 10, -80, 46, -50 + fx, 78);
    ctx.quadraticCurveTo(-14 + fx, 104, fx * 1.2, 106);
    ctx.quadraticCurveTo(14 + fx, 104, 50 + fx, 78);
    ctx.bezierCurveTo(80, 46, 90 + fx * 0.3, 10, 86 + fx * 0.4, -50);
    ctx.closePath();
    const fg = ctx.createLinearGradient(0, -60, 0, 110);
    fg.addColorStop(0, C.skinSh); fg.addColorStop(0.3, C.skin); fg.addColorStop(1, C.skin);
    ctx.fillStyle = fg; ctx.fill(); ctx.strokeStyle = C.skinLine; ctx.lineWidth = 2; ctx.stroke();
    // allık
    const blush = 0.25 + (pose.blush || 0) * 0.6;
    for (const s of [-1, 1]) {
      const bg = ctx.createRadialGradient(s * 50 + fx, 42, 2, s * 50 + fx, 42, 26);
      bg.addColorStop(0, C.blush + (blush * 0.7) + ")"); bg.addColorStop(1, C.blush + "0)");
      ctx.fillStyle = bg; ctx.beginPath(); ctx.ellipse(s * 50 + fx, 42, 28, 16, 0, 0, TAU); ctx.fill();
      if ((pose.blush || 0) > 0.4) {
        ctx.strokeStyle = "rgba(230,60,90,0.6)"; ctx.lineWidth = 1.6;
        for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.moveTo(s * 50 + fx + k * 9 - 3, 47); ctx.lineTo(s * 50 + fx + k * 9 + 3, 37); ctx.stroke(); }
      }
    }
    // gözler
    const blink = pose.blink || 0;
    for (const s of [-1, 1]) this.drawEye(ctx, s * 38 + fx * (1 + s * turn * 0.2), 10, s, 1 - Math.max(blink, s === 1 ? (pose.wink || 0) : 0), pose);
    // kaşlar
    const brow = pose.brow || 0; // + sinirli, - endişeli
    for (const s of [-1, 1]) {
      ctx.beginPath();
      const x0 = s * 18 + fx, x1 = s * 62 + fx;
      ctx.moveTo(x0, -26 + brow * 6 - (pose.browUp || 0) * 8);
      ctx.quadraticCurveTo((x0 + x1) / 2, -36 - (pose.browUp || 0) * 8, x1, -28 - brow * 3);
      ctx.strokeStyle = "#8e1e26"; ctx.lineWidth = 3.4; ctx.lineCap = "round"; ctx.stroke();
    }
    // burun
    ctx.beginPath(); ctx.moveTo(2 + fx * 1.3, 44); ctx.quadraticCurveTo(-3 + fx * 1.3, 50, 1 + fx * 1.3, 52);
    ctx.strokeStyle = C.skinLine; ctx.lineWidth = 1.6; ctx.stroke();
    // ağız
    this.drawMouth(ctx, fx * 1.2, 74, pose);
    // perçemler ve kafa üstü
    this.drawBangs(ctx, pose);
    ctx.restore();
  }

  drawEye(ctx, cx, cy, s, open, pose) {
    const w = 25, h = 22 * clamp(open, 0, 1);
    const look = pose.look || [0, 0];
    ctx.save();
    if (open < 0.15) {
      ctx.beginPath(); ctx.moveTo(cx - w, cy + 2); ctx.quadraticCurveTo(cx, cy + 10 * (pose.happyEyes ? -1 : 1) + 4, cx + w, cy + 2 - s * 0);
      ctx.strokeStyle = "#2a0a10"; ctx.lineWidth = 4; ctx.lineCap = "round"; ctx.stroke();
      ctx.restore(); return;
    }
    const inner = cx - s * w, outer = cx + s * w;
    const slant = 6;
    // sklera
    ctx.beginPath();
    ctx.moveTo(inner, cy + 4);
    ctx.bezierCurveTo(inner + s * 8, cy - h * 1.05, outer - s * 10, cy - h * 1.15 - slant, outer, cy - slant + 2);
    ctx.bezierCurveTo(outer - s * 6, cy + h * 0.9, inner + s * 10, cy + h * 0.95, inner, cy + 4);
    ctx.closePath();
    ctx.fillStyle = "#fff"; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = "rgba(120,130,190,0.25)"; ctx.fillRect(cx - 40, cy - 40, 80, 18);
    // iris
    const ix = cx + look[0] * 6 + s * 1, iy = cy + 2 + look[1] * 4;
    const ig = ctx.createLinearGradient(0, iy - 22, 0, iy + 22);
    ig.addColorStop(0, C.irisD); ig.addColorStop(0.45, C.iris); ig.addColorStop(1, C.irisL);
    ctx.beginPath(); ctx.ellipse(ix, iy, 16.5, 21, 0, 0, TAU); ctx.fillStyle = ig; ctx.fill();
    ctx.strokeStyle = "#063238"; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(ix, iy + 1, 11, 14, 0, 0, TAU); ctx.strokeStyle = "rgba(160,255,240,0.35)"; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(ix, iy, 6.5 * (pose.pupil || 1), 10 * (pose.pupil || 1), 0, 0, TAU); ctx.fillStyle = C.pupil; ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.beginPath(); ctx.ellipse(ix - 6, iy - 9, 5.5, 7, -0.4, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.arc(ix + 6, iy + 9, 2.6, 0, TAU); ctx.fill();
    ctx.globalAlpha = 0.6; ctx.beginPath(); ctx.arc(ix + 8, iy - 3, 1.6, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
    ctx.restore();
    // üst kirpik
    ctx.beginPath();
    ctx.moveTo(inner - s * 2, cy + 5);
    ctx.bezierCurveTo(inner + s * 8, cy - h * 1.08, outer - s * 10, cy - h * 1.18 - slant, outer + s * 4, cy - slant + 1);
    ctx.strokeStyle = "#240810"; ctx.lineWidth = 5.5; ctx.lineCap = "round"; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(outer, cy - slant); ctx.lineTo(outer + s * 11, cy - slant - 7); ctx.moveTo(outer - s * 4, cy - h - 2); ctx.lineTo(outer + s * 5, cy - h - 10);
    ctx.lineWidth = 3; ctx.stroke();
    // alt kirpik
    ctx.beginPath(); ctx.moveTo(outer - s * 2, cy - slant + 6); ctx.bezierCurveTo(outer - s * 8, cy + h * 0.85, inner + s * 16, cy + h * 0.9, inner + s * 10, cy + h * 0.75);
    ctx.strokeStyle = "rgba(90,20,30,0.75)"; ctx.lineWidth = 1.6; ctx.stroke();
    // göz kapağı çizgisi
    ctx.beginPath(); ctx.moveTo(inner + s * 6, cy - h * 1.15 - 2); ctx.quadraticCurveTo(cx, cy - h * 1.45 - 4, outer - s * 2, cy - h * 1.1 - slant);
    ctx.strokeStyle = "rgba(150,70,70,0.55)"; ctx.lineWidth = 1.4; ctx.stroke();
    ctx.restore();
  }

  drawMouth(ctx, x, y, pose) {
    const open = clamp(pose.mouth || 0, 0, 1), smile = pose.smile ?? 0.6;
    ctx.save();
    if (open > 0.06) {
      const w = 11 + open * 3 + smile * 2, h = 3 + open * 12;
      ctx.beginPath();
      ctx.moveTo(x - w, y - smile * 2);
      ctx.quadraticCurveTo(x, y - 2 - smile * 1, x + w, y - smile * 2);
      ctx.quadraticCurveTo(x, y + h * 1.4, x - w, y - smile * 2);
      ctx.fillStyle = "#7a1a26"; ctx.fill(); ctx.strokeStyle = "#4a0a12"; ctx.lineWidth = 1.6; ctx.stroke();
      ctx.save(); ctx.clip();
      ctx.beginPath(); ctx.ellipse(x, y + h * 0.95, w * 0.6, h * 0.45, 0, 0, TAU); ctx.fillStyle = "#e5707a"; ctx.fill();
      ctx.restore();
    } else {
      ctx.beginPath();
      if (pose.pout) { ctx.moveTo(x - 8, y + 2); ctx.quadraticCurveTo(x, y - 4, x + 8, y + 2); }
      else { ctx.moveTo(x - 13, y - smile * 4); ctx.quadraticCurveTo(x, y + smile * 6, x + 13 + smile * 2, y - smile * 6); }
      ctx.strokeStyle = "#8a2a32"; ctx.lineWidth = 2.6; ctx.lineCap = "round"; ctx.stroke();
    }
    ctx.restore();
  }

  drawBangs(ctx, pose) {
    // kafa üstü
    const g = ctx.createLinearGradient(0, -130, 0, 0);
    g.addColorStop(0, C.hairL); g.addColorStop(0.6, C.hair); g.addColorStop(1, C.hairD);
    ctx.beginPath();
    ctx.moveTo(-100, 10);
    ctx.bezierCurveTo(-118, -70, -70, -136, 0, -134);
    ctx.bezierCurveTo(70, -136, 118, -70, 100, 10);
    // perçem uçları (sağdan sola)
    const tips = [[92, 30], [70, -18], [58, 0], [44, -30], [30, -8], [14, -34], [-4, -12], [-18, -36], [-34, -6], [-50, -30], [-64, -2], [-76, -24], [-94, 30]];
    let prev = [100, 10];
    for (let i = 0; i < tips.length; i++) {
      const tp = tips[i];
      const notch = i % 2 === 1;
      const cxp = (prev[0] + tp[0]) / 2 + (notch ? 0 : 4), cyp = notch ? Math.min(prev[1], tp[1]) - 18 : (prev[1] + tp[1]) / 2;
      ctx.quadraticCurveTo(cxp, cyp, tp[0], tp[1] + 8);
      prev = tp;
    }
    ctx.closePath();
    ctx.fillStyle = g; ctx.fill(); ctx.strokeStyle = C.hairLine; ctx.lineWidth = 2; ctx.stroke();
    // perçem çizgileri
    ctx.strokeStyle = "rgba(70,0,12,0.55)"; ctx.lineWidth = 1.5;
    for (const [x0, x1] of [[-10, -18], [20, 14], [-40, -50], [48, 58], [-70, -76], [76, 70]]) {
      ctx.beginPath(); ctx.moveTo(x0 * 0.4, -120); ctx.quadraticCurveTo(x0, -70, x1, -20); ctx.stroke();
    }
    // melek halkası parlaklığı
    ctx.beginPath();
    for (let i = 0; i <= 12; i++) { const a = lerp(-2.45, -0.7, i / 12); const rr = 92 + (i % 2) * 7; const p = [Math.cos(a) * rr, -30 + Math.sin(a) * rr * 0.86]; i ? ctx.lineTo(...p) : ctx.moveTo(...p); }
    ctx.strokeStyle = "rgba(255,170,170,0.55)"; ctx.lineWidth = 6; ctx.lineJoin = "round"; ctx.stroke();
    // yüzü çevreleyen yan perçemler
    for (const s of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(s * 60, -80);
      ctx.bezierCurveTo(s * 108, -40, s * 98, 60, s * 80, 140);
      ctx.bezierCurveTo(s * 76, 80, s * 70, 30, s * 68, -10);
      ctx.closePath();
      const sg = ctx.createLinearGradient(0, -80, 0, 140);
      sg.addColorStop(0, C.hair); sg.addColorStop(1, C.hairL);
      ctx.fillStyle = sg; ctx.fill(); ctx.strokeStyle = C.hairLine; ctx.lineWidth = 1.8; ctx.stroke();
    }
    // ahoge
    ctx.save(); ctx.translate(6, -128); ctx.rotate(this.ahoge.a);
    ctx.beginPath();
    ctx.moveTo(-6, 4); ctx.bezierCurveTo(-14, -40, 10, -78, 42, -66);
    ctx.bezierCurveTo(52, -62, 52, -48, 40, -50);
    ctx.bezierCurveTo(16, -58, 2, -34, 6, 4);
    ctx.closePath(); ctx.fillStyle = C.hair; ctx.fill(); ctx.strokeStyle = C.hairLine; ctx.lineWidth = 1.8; ctx.stroke();
    ctx.restore();
  }

  drawArm(ctx, a) {
    const { S, E, W, s } = a;
    const pts = [S, [lerp(S[0], E[0], 0.5), lerp(S[1], E[1], 0.5)], E, [lerp(E[0], W[0], 0.5), lerp(E[1], W[1], 0.5)], W];
    const rad = [29, 25, 21, 19, 17];
    const sh = ribbon(pts, rad, true, false);
    const g = ctx.createLinearGradient(S[0] - 40, S[1], S[0] + 40, S[1] + 40);
    g.addColorStop(0, C.blazer); g.addColorStop(0.5, "#28232f"); g.addColorStop(1, C.blazerD);
    // el (kolun arkasında değil, ucunda)
    this.drawHand(ctx, W, a.handA, s, a.hand);
    fillPath(ctx, sh, g, "#000", 2);
    // dirsek kırışığı
    ctx.beginPath(); ctx.arc(E[0], E[1], 12, 0, Math.PI); ctx.strokeStyle = "rgba(160,150,200,0.35)"; ctx.lineWidth = 1.5; ctx.stroke();
    // manşet
    const d = norm(W[0] - E[0], W[1] - E[1]);
    const c0 = [W[0] - d[0] * 4, W[1] - d[1] * 4];
    ctx.beginPath();
    ctx.moveTo(c0[0] - d[1] * 18, c0[1] + d[0] * 18); ctx.lineTo(c0[0] + d[1] * 18, c0[1] - d[0] * 18);
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 9; ctx.stroke();
  }

  drawHand(ctx, W, ang, s, shape) {
    ctx.save(); ctx.translate(W[0], W[1]); ctx.rotate(ang - Math.PI / 2);
    // yerel: +y parmaklara doğru
    ctx.fillStyle = C.skin; ctx.strokeStyle = C.skinLine; ctx.lineWidth = 1.6;
    ctx.beginPath();
    if (shape === "fist") {
      ctx.ellipse(0, 22, 20, 22, 0, 0, TAU);
    } else if (shape === "point") {
      ctx.moveTo(-16, 0); ctx.lineTo(16, 0); ctx.quadraticCurveTo(22, 26, 14, 40); ctx.lineTo(6, 42);
      ctx.lineTo(6, 76); ctx.quadraticCurveTo(0, 82, -5, 76); ctx.lineTo(-5, 42); ctx.quadraticCurveTo(-20, 38, -18, 20); ctx.closePath();
    } else {
      ctx.moveTo(-17, 0); ctx.lineTo(17, 0);
      ctx.quadraticCurveTo(21, 30, 18, 46); ctx.quadraticCurveTo(14, 70, 6, 76);
      ctx.quadraticCurveTo(-4, 80, -12, 72); ctx.quadraticCurveTo(-20, 50, -18, 30); ctx.closePath();
    }
    ctx.fill(); ctx.stroke();
    if (shape !== "fist") {
      // parmak ayrımları
      ctx.strokeStyle = "rgba(190,120,110,0.7)"; ctx.lineWidth = 1.2;
      if (shape === "open") for (const x of [-6, 2, 10]) { ctx.beginPath(); ctx.moveTo(x, 46); ctx.lineTo(x * 0.9, 70); ctx.stroke(); }
      // başparmak
      const tx = -s * 17;
      ctx.beginPath(); ctx.moveTo(tx, 10); ctx.quadraticCurveTo(tx - s * 16, 26, tx - s * 12, 42); ctx.quadraticCurveTo(tx - s * 4, 44, tx, 30);
      ctx.fillStyle = C.skin; ctx.fill(); ctx.strokeStyle = C.skinLine; ctx.stroke();
    }
    ctx.restore();
  }

  drawWings(ctx, r, pose) {
    const o = clamp(pose.wings, 0, 1);
    const flap = Math.sin(this.t * 2.6) * 0.12 * o + (pose.wingFlap || 0);
    for (const s of [-1, 1]) {
      const root = M.ap(r.C, s * 40, -1140);
      ctx.save(); ctx.translate(root[0], root[1]); ctx.rotate(r.bodyA); ctx.scale(s, 1);
      ctx.rotate(-flap);
      const sc = 0.25 + 0.75 * o;
      ctx.scale(sc, sc);
      const ang0 = lerp(-0.2, -0.75, o);
      const E = [Math.cos(ang0) * 230, Math.sin(ang0) * 230];
      const W = [E[0] + Math.cos(ang0 - 0.55) * 200, E[1] + Math.sin(ang0 - 0.55) * 200];
      const fingers = [[-0.1, 300], [0.45, 420], [0.95, 470], [1.45, 430], [1.9, 330]];
      const tips = fingers.map(([a, l]) => [W[0] + Math.cos(a) * l * lerp(0.5, 1, o), W[1] + Math.sin(a) * l * lerp(0.5, 1, o)]);
      const bodyPt = [10, 230];
      // zar
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(...E); ctx.lineTo(...W); ctx.lineTo(...tips[0]);
      for (let i = 1; i < tips.length; i++) {
        const a = tips[i - 1], b = tips[i];
        const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
        const toW = [W[0] - m[0], W[1] - m[1]];
        ctx.quadraticCurveTo(m[0] + toW[0] * 0.28, m[1] + toW[1] * 0.28, b[0], b[1]);
      }
      { const a = tips[tips.length - 1], m = [(a[0] + bodyPt[0]) / 2, (a[1] + bodyPt[1]) / 2]; ctx.quadraticCurveTo(m[0] + 40, m[1] - 60, ...bodyPt); }
      ctx.closePath();
      const g = ctx.createRadialGradient(W[0], W[1], 20, W[0], W[1], 480);
      g.addColorStop(0, "#2c0d30"); g.addColorStop(0.6, "#140611"); g.addColorStop(1, "#3a0612");
      ctx.fillStyle = g; ctx.globalAlpha = 0.97; ctx.fill(); ctx.globalAlpha = 1;
      ctx.strokeStyle = "rgba(230,40,60,0.75)"; ctx.lineWidth = 3; ctx.stroke();
      // kemikler
      ctx.strokeStyle = "#050205"; ctx.lineCap = "round";
      ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(...E); ctx.lineTo(...W); ctx.stroke();
      ctx.lineWidth = 6;
      for (const tp of tips) { ctx.beginPath(); ctx.moveTo(...W); ctx.lineTo(...tp); ctx.stroke(); }
      ctx.strokeStyle = "rgba(255,80,90,0.5)"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, -4); ctx.lineTo(E[0], E[1] - 4); ctx.lineTo(W[0], W[1] - 4); ctx.stroke();
      // pençe
      ctx.beginPath(); ctx.moveTo(W[0], W[1]); ctx.lineTo(W[0] + 12, W[1] - 34); ctx.lineTo(W[0] + 16, W[1] - 4); ctx.fillStyle = "#050205"; ctx.fill();
      ctx.restore();
    }
  }

  // silüet merkezleri (aura için)
  anchors(pose) {
    const r = this.rig(pose);
    return { head: M.ap(r.H, 0, 0), chest: r.torso(0, -1080), hip: M.ap(r.P, 0, -830), hands: [r.arms.l.W, r.arms.r.W], feet: [r.legs.l.A, r.legs.r.A] };
  }
}

function norm(x, y) { const l = Math.hypot(x, y) || 1; return [x / l, y / l]; }

// iki kemikli ters kinematik; dirsek/diz s yönüne doğru büker
function ik2(S, T, L1, L2, s, bendScale, down) {
  let dx = T[0] - S[0], dy = T[1] - S[1];
  let d = Math.hypot(dx, dy);
  const maxd = L1 + L2 - 0.5;
  if (d > maxd) { dx *= maxd / d; dy *= maxd / d; d = maxd; }
  d = Math.max(d, Math.abs(L1 - L2) + 1);
  const base = Math.atan2(dy, dx);
  const c = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1);
  const off = Math.acos(c);
  const k1 = [S[0] + Math.cos(base + off) * L1, S[1] + Math.sin(base + off) * L1];
  const k2 = [S[0] + Math.cos(base - off) * L1, S[1] + Math.sin(base - off) * L1];
  let K = down ? (k1[1] > k2[1] ? k1 : k2) : ((k1[0] * s > k2[0] * s) ? k1 : k2);
  const mid = [S[0] + dx * L1 / (L1 + L2), S[1] + dy * L1 / (L1 + L2)];
  K = [lerp(mid[0], K[0], bendScale), lerp(mid[1], K[1], bendScale)];
  return [K, [S[0] + dx, S[1] + dy]];
}

window.Character = Character;
window.CharUtil = { lerp, clamp, smooth, M, smoothPath, TAU };
