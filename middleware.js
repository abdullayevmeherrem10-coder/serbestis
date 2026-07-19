// Vercel Edge Middleware — kitab səhifələri yalnız daxil olmuş istifadəçilərə açıqdır.
// Girişdə sayt "kabinet" cookie-sinə HMAC-imzalı token yazır; burada yoxlanılır.
// Tam imza yoxlanışı üçün Vercel-də CABINET_SECRET env dəyişəni təyin olunmalıdır
// (o zaman API tokenləri də həmin sirlə imzalanır).

export const config = { matcher: ['/kitab/:path*', '/kitab.html', '/kollokvium/:path*'] };

// Tokeni yoxlayır və payload-ı ({id, role, exp}) qaytarır (etibarsızsa null).
async function tokenPayload(token, secret) {
    if (!token || token.indexOf('.') === -1) return null;
    const [b, sig] = token.split('.');
    if (!b || !sig) return null;
    let payload;
    try {
        const pad = '='.repeat((4 - (b.length % 4)) % 4);
        payload = JSON.parse(atob(b.replace(/-/g, '+').replace(/_/g, '/') + pad));
    } catch (e) {
        return null;
    }
    if ((payload.exp || 0) <= Date.now() / 1000) return null;
    if (!secret) {
        // Sirr yoxdursa yalnız format yoxlanışı (zəif fallback)
        return sig.length >= 16 ? payload : null;
    }
    try {
        const enc = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw', enc.encode(secret),
            { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
        );
        const mac = await crypto.subtle.sign('HMAC', key, enc.encode(b));
        const hex = Array.from(new Uint8Array(mac)).map(x => x.toString(16).padStart(2, '0')).join('').slice(0, 32);
        return hex === sig ? payload : null;
    } catch (e) {
        return null;
    }
}

export default async function middleware(req) {
    const cookie = req.headers.get('cookie') || '';
    const m = cookie.match(/(?:^|;\s*)kabinet=([^;]+)/);
    const token = m ? decodeURIComponent(m[1]) : '';
    const url = new URL(req.url);
    const payload = await tokenPayload(token, process.env.CABINET_SECRET || '');

    const isKollok = url.pathname.startsWith('/kollokvium/');
    // Kollokvium yalnız müəllimə; kitab hər daxil olmuş istifadəçiyə
    const ok = payload && (!isKollok || payload.role === 'teacher');
    if (ok) return;

    // HTML səhifələr ana səhifəyə yönləndirilir, digər fayllar 401
    if (url.pathname === '/kitab.html' || url.pathname === '/kollokvium/' || url.pathname.endsWith('/kollokvium/index.html')) {
        return Response.redirect(new URL('/', req.url), 302);
    }
    return new Response('Giriş tələb olunur.', {
        status: 401,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
    });
}
