AIEditor local vendor assets

Location
- CSS: `backend/static/admin_portal/vendor/aieditor/style.css`
- JS (UMD): `backend/static/admin_portal/vendor/aieditor/aieditor.umd.js`

Pinned version
- `aieditor@1.4.2`

Source
- `https://unpkg.com/aieditor@1.4.2/dist/style.css`
- `https://unpkg.com/aieditor@1.4.2/dist/index.umd.js`

Why UMD
- Admin pages load plain browser scripts.
- UMD exposes `window.AiEditor` directly, no bundler required.

Upgrade steps
1. Download new `style.css` and `index.umd.js` from the target version.
2. Replace local files in this directory.
3. Update `?v=` query string in `admin_portal/templates/admin_portal/base.html`.
4. Run `python manage.py collectstatic --noinput`.
