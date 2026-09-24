# Privacy Policy

HomePortal is a self-hosted application. Everything it stores stays in the
data folder on your own server:

- `portal.json`: your links, page texts and appearance settings
- `auth.json`: a hash of the admin password, never the password itself
- `uploads/`: background images you uploaded, saved again without location or camera data
- `photos/`: your album pictures, which HomePortal only reads

- **No telemetry:** HomePortal does not collect usage data or phone home.
- **No external requests:** fonts, patterns and background photos are bundled; nothing loads from the internet.
- **One cookie:** a session cookie for the logged-in admin. Visitors who only view the page get none.
- **Who can see it:** anyone who can reach the port on your network, unless you require the password for viewing in the settings. Do not expose it to the internet without that, since your photos are on it.
