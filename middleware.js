// Vercel Edge Middleware — kitab səhifələri yalnız daxil olmuş istifadəçilərə açıqdır.
// Girişdə sayt "kabinet" cookie-sinə HMAC-imzalı token yazır; burada yoxlanılır.
// Tam imza yoxlanışı üçün Vercel-də CABINET_SECRET env dəyişəni təyin olunmalıdır
// (o zaman API tokenləri də həmin sirlə imzalanır).

export const config = { matcher: ['/kitab/:path*', '/kitab.html'] };

async function validToken(token, secret) {
    if (!token || token.indexOf('.') === -1) return false;
    const [b, sig] = token.split('.');
    if (!b || !sig) return false;
    if (!secret) {
        // Sirr təyin olunmayıbsa yalnız format yoxlanışı (zəif, amma kənar girişi kəsir)
        return sig.length >= 16;
    }
    try {
        const enc = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw', enc.encode(secret),
            { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
        );
        const mac = await crypto.subtle.sign('HMAC', key, enc.encode(b));
        const hex = Array.from(new Uint8Array(mac)).map(x => x.toString(16).padStart(2, '0')).join('').slice(0, 32);
        if (hex !== sig) return false;
        const pad = '='.repeat((4 - (b.length % 4)) % 4);
        const payload = JSON.parse(atob(b.replace(/-/g, '+').replace(/_/g, '/') + pad));
        return (payload.exp || 0) > Date.now() / 1000;
    } catch (e) {
        return false;
    }
}

export default async function middleware(req) {
    const cookie = req.headers.get('cookie') || '';
    const m = cookie.match(/(?:^|;\s*)kabinet=([^;]+)/);
    const token = m ? decodeURIComponent(m[1]) : '';
    const ok = await validToken(token, process.env.CABINET_SECRET || '');
    if (ok) return; // davam et — statik fayl verilir

    const url = new URL(req.url);
    if (url.pathname === '/kitab.html') {
        return Response.redirect(new URL('/', req.url), 302);
    }
    return new Response('Giriş tələb olunur.', {
        status: 401,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
    });
}
