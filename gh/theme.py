"""Gemeinsames Design (Liquid Glass) für alle Seiten. Reines CSS, keine Skripte, keine externen Fonts."""

BASE = r"""
:root{
  --bg:#06070a;--text:#f3f5f9;--muted:rgba(235,240,255,.62);--faint:rgba(235,240,255,.38);
  --accent:#22d3ee;--accent2:#e440d0;--on-accent:#03161b;--good:#3ee8a0;--bad:#ff6b8b;
  --glass:linear-gradient(140deg,rgba(255,255,255,.13),rgba(255,255,255,.035) 55%,rgba(255,255,255,.07));
  --glass-strong:linear-gradient(140deg,rgba(255,255,255,.2),rgba(255,255,255,.06) 60%,rgba(255,255,255,.1));
  --edge:rgba(255,255,255,.16);--edge-hi:rgba(255,255,255,.42);--chip:rgba(255,255,255,.08);
  --shadow:0 18px 50px -18px rgba(0,0,0,.65),0 2px 6px rgba(0,0,0,.25);
  --blur:saturate(180%) blur(22px);--r:24px;--spring:cubic-bezier(.34,1.56,.64,1);
  --blob1:rgba(34,211,238,.38);--blob2:rgba(228,64,208,.34);--blob3:rgba(99,102,241,.28);--pattern-o:.06;
}
@media (prefers-color-scheme: light){:root{
  --bg:#eef0f6;--text:#0d0f14;--muted:rgba(13,15,20,.6);--faint:rgba(13,15,20,.4);
  --accent:#0e7490;--accent2:#b0179c;--on-accent:#fff;--good:#0f7a4e;--bad:#c0264a;
  --glass:linear-gradient(140deg,rgba(255,255,255,.78),rgba(255,255,255,.5) 55%,rgba(255,255,255,.66));
  --glass-strong:linear-gradient(140deg,rgba(255,255,255,.92),rgba(255,255,255,.66));
  --edge:rgba(255,255,255,.9);--edge-hi:#fff;--chip:rgba(13,15,20,.06);
  --shadow:0 18px 44px -20px rgba(40,44,80,.35),0 2px 6px rgba(40,44,80,.08);
  --blob1:rgba(34,211,238,.32);--blob2:rgba(228,64,208,.24);--blob3:rgba(99,102,241,.2);--pattern-o:.05;
}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{margin:0;min-height:100vh;min-height:100dvh;background:var(--bg);color:var(--text);
  font:16px/1.5 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI Variable","Segoe UI",Roboto,system-ui,sans-serif;
  font-feature-settings:"ss01","cv11";-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit}
h1,h2,h3{letter-spacing:-.025em;line-height:1.15}
/* Hintergrund: langsam treibende Farbflächen hinter dem Glas + Logo-Muster */
.aurora{position:fixed;inset:-20vmax;z-index:-2;pointer-events:none;filter:blur(60px)}
.aurora i{position:absolute;width:60vmax;height:60vmax;border-radius:50%;opacity:.9;will-change:transform}
.aurora i:nth-child(1){left:-5%;top:0;background:radial-gradient(circle,var(--blob1),transparent 62%);animation:drift1 26s ease-in-out infinite alternate}
.aurora i:nth-child(2){right:-10%;top:20%;background:radial-gradient(circle,var(--blob2),transparent 62%);animation:drift2 32s ease-in-out infinite alternate}
.aurora i:nth-child(3){left:20%;bottom:-15%;background:radial-gradient(circle,var(--blob3),transparent 62%);animation:drift3 38s ease-in-out infinite alternate}
.pattern{position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:var(--pattern-o);
  background:url(/assets/pattern.webp) 0 0/420px auto;
  -webkit-mask-image:linear-gradient(to bottom,#000,transparent 75%);mask-image:linear-gradient(to bottom,#000,transparent 75%)}
@media (prefers-color-scheme: light){.pattern{filter:invert(1)}}
@keyframes drift1{to{transform:translate(18vmax,12vmax) scale(1.15)}}
@keyframes drift2{to{transform:translate(-16vmax,10vmax) scale(.9)}}
@keyframes drift3{to{transform:translate(10vmax,-14vmax) scale(1.1)}}
/* Glas-Fläche mit Lichtkante */
.glass{position:relative;background:var(--glass);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);
  border:1px solid var(--edge);border-radius:var(--r);box-shadow:var(--shadow),inset 0 1px 0 var(--edge-hi),inset 0 -1px 0 rgba(255,255,255,.04)}
.glass::before{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;
  background:radial-gradient(120% 60% at 15% -10%,rgba(255,255,255,.22),transparent 55%);mix-blend-mode:soft-light}
.press{transition:transform .45s var(--spring),box-shadow .3s,border-color .3s}
@media (hover:hover){.press:hover{transform:translateY(-2px) scale(1.01);border-color:var(--edge-hi)}}
.press:active{transform:scale(.97);transition-duration:.12s}
.rise{animation:rise .7s var(--spring) both;animation-delay:calc(var(--i,0)*55ms)}
@keyframes rise{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){.aurora i,.rise{animation:none}.press{transition:none}}
.wordmark{height:44px;width:auto;display:block}
.chip{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;text-decoration:none;
  font-size:14px;font-weight:650;white-space:nowrap}
.chip.on{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-color:transparent;
  box-shadow:0 8px 22px -8px var(--accent2),inset 0 1px 0 rgba(255,255,255,.5)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:9px 16px;border-radius:999px;
  background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 55%,var(--accent2)));color:var(--on-accent);
  text-decoration:none;font-weight:750;font-size:14px;box-shadow:0 8px 20px -10px var(--accent),inset 0 1px 0 rgba(255,255,255,.45)}
.tag{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--accent2);
  vertical-align:middle}
.muted{color:var(--muted)}.sub{color:var(--muted);margin:0 0 18px}
.ad{font-size:12.5px;color:var(--muted);padding:10px 14px;border-radius:16px;margin:0 0 18px}
.ad b{color:var(--accent2)}
footer{margin:36px 0 calc(16px + env(safe-area-inset-bottom));color:var(--faint);font-size:12px;line-height:1.6}
footer a{color:var(--muted)}
"""
