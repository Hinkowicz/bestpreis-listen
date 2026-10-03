/* Weiterleitung zu Amazon: öffnet möglichst die Amazon-App, sonst amazon.de – immer mit Partner-Tag. Kein Tracking. */
(function () {
  const TAG = 'hinkowicz-21';
  const SHOP = 'hinkowicz'; // amazon.de/shop/hinkowicz
  const q = new URLSearchParams(location.search);
  const shop = q.has('shop');
  const asin = (q.get('i') || '').trim().toUpperCase();
  const $ = id => document.getElementById(id);
  if (!shop && !/^[A-Z0-9]{10}$/.test(asin)) {
    $('t').textContent = 'Link ungültig';
    $('s').textContent = 'Dieser Amazon-Link ist leider kaputt.';
    $('app').remove(); $('h').hidden = true;
    $('web').textContent = 'Zu hinkowicz.de'; $('web').href = '/';
    return;
  }
  const path = shop ? `www.amazon.de/shop/${SHOP}?tag=${TAG}&language=de_DE` : `www.amazon.de/dp/${asin}?tag=${TAG}`;
  const web = 'https://' + path;
  const ua = navigator.userAgent || '';
  const android = /Android/i.test(ua);
  const ios = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  // In-App-Browser (TikTok, Instagram, Facebook …) blockieren oft den Sprung in andere Apps
  const inApp = /musical_ly|BytedanceWebview|TikTok|Instagram|FBAN|FBAV|Snapchat|Twitter|LinkedInApp|Pinterest/i.test(ua);
  const app = android
    ? `intent://${path}#Intent;scheme=https;package=com.amazon.mShop.android.shopping;S.browser_fallback_url=${encodeURIComponent(web)};end`
    : ios ? 'com.amazon.mobile.shopping.web://' + path : web;

  $('app').href = app;
  $('web').href = web;
  $('h').hidden = !inApp;

  if (!android && !ios) { location.replace(web); return; } // Computer: direkt zu amazon.de

  let left = false;
  document.addEventListener('visibilitychange', () => { if (document.hidden) left = true; });
  location.href = app; // Android fällt ohne App selbst auf amazon.de zurück
  setTimeout(() => {
    if (left) return; // App hat sich geöffnet
    $('t').textContent = 'Fast geschafft';
    $('s').textContent = inApp ? 'Diese App lässt den Sprung zu Amazon leider nicht automatisch zu.' : 'Tippe auf den Button, um den Deal zu öffnen.';
    if (ios && !inApp) location.href = web; // ohne installierte App: amazon.de im Browser (öffnet die App, falls vorhanden)
  }, 1500);
})();
