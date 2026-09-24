# Privacy Policy

HomePortal is a self-hosted application. Everything it stores stays in the
data folder on your own server:

- `portal.json`: your tabs, tiles, page texts and appearance settings
- `auth.json`: a hash of the admin password, never the password itself
- `connections.json`: the Home Assistant address and access token, readable only by the file owner
- `uploads/`: background images you uploaded, saved again without location or camera data
- `photos/`: your album pictures, which HomePortal only reads

- **No telemetry:** HomePortal does not collect usage data or phone home.
- **Requests from the server:** Home Assistant tiles ask your Home Assistant, status tiles ask the addresses you entered whether they answer (nothing is read from them), both from the portal server, never from the browser.
- **One request to the internet, only if you add it:** a weather tile sends the coordinates of its place to [Open-Meteo](https://open-meteo.com) every 15 minutes, and the place name once when you save the tile. Without a weather tile, nothing leaves your network.
- **Bundled assets:** fonts, patterns and background photos load from your server.
- **One cookie:** a session cookie for the logged-in admin. Visitors who only view the page get none.
- **Who can see it:** anyone who can reach the port on your network, unless you require the password for viewing in the settings. Do not expose it to the internet without that, since your photos are on it.
