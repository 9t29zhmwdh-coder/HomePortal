# Getting Started with Home Portal

This guide is for people with **no coding experience**. It walks you through every step, from opening a terminal to seeing your Home Portal running in the browser.

Home Portal runs inside [Docker](https://www.docker.com/), a tool that packages the whole app (the FastAPI backend and an Nginx reverse proxy) so it runs the same way on every machine. You do not need to install Python or a web server by hand.

> Home Portal is designed to run on a NAS or a Linux server that stays on permanently, but you can also try it out on a regular desktop machine. Pick the section for your operating system below.

---

## Windows

### 1. Open a terminal

Right-click the **Start** button and choose **Terminal** (or **Windows PowerShell** on older Windows versions).

### 2. Check whether Docker is installed

```powershell
docker --version
docker compose version
```

- Version numbers shown → continue to step 3.
- `'docker' is not recognized as the name of a cmdlet...` → Docker Desktop is not installed yet.

**Install Docker Desktop:**

1. Download it from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
2. Run the installer, accept the defaults, and allow it to enable **WSL2** if asked.
3. Restart your computer if prompted.
4. Start **Docker Desktop** and wait until the whale icon in the system tray shows it is running.
5. Re-run the two commands above in your terminal.

### 3. Download Home Portal

No-Git route:

1. Go to [github.com/9t29zhmwdh-coder/HomePortal](https://github.com/9t29zhmwdh-coder/HomePortal).
2. Click the green **Code** button → **Download ZIP**.
3. Extract it (right-click → **Extract All...**), e.g. to `Documents\HomePortal`.

Or, with Git:

```powershell
git clone https://github.com/9t29zhmwdh-coder/HomePortal.git
```

### 4. Move into the folder

```powershell
cd Documents\HomePortal
```

(Tip: type `cd ` with a trailing space, then drag the folder from File Explorer into the terminal to auto-fill the path.)

### 5. Create and edit your configuration file

Home Portal needs a `.env` file with two settings: the folder where it keeps its settings and your photos, and your timezone.

```powershell
copy .env.example .env
notepad .env
```

In Notepad, set:
- `DATA_PATH`: the folder for settings, uploads and `photos\`, e.g. `C:\HomePortal-data`
- `TZ`: your timezone, e.g. `Europe/Zurich`

Save and close Notepad.

### 6. Build and start Home Portal

```powershell
docker compose up -d --build
```

The first run downloads and builds everything, this can take a few minutes.

### 7. Open the portal

Go to `http://localhost` in your browser (or the address/hostname of the machine running Docker, if it's not your local one).

---

## Linux

### 1. Open a terminal

Depends on your desktop environment: usually `Ctrl+Alt+T`, or search "Terminal" in your application menu. On a NAS, you may need to enable SSH access first and connect from another computer.

### 2. Check whether Docker is installed

```bash
docker --version
docker compose version
```

- Version numbers shown → continue to step 3.
- `command not found` → install Docker via your distro's package manager. See [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) for your specific distribution. Debian/Ubuntu-based systems can typically use:

```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and back in afterwards so your user can run Docker without `sudo`.

If you're using a NAS (Synology, QNAP, etc.), install Docker via the NAS's own package center/app store instead, then use its built-in terminal or SSH access for the following steps.

### 3. Download Home Portal

No-Git route: download the ZIP from [github.com/9t29zhmwdh-coder/HomePortal](https://github.com/9t29zhmwdh-coder/HomePortal) (green **Code** button → **Download ZIP**) and extract it.

Or, with Git:

```bash
git clone https://github.com/9t29zhmwdh-coder/HomePortal.git
cd HomePortal
```

### 4. Create and edit your configuration file

```bash
cp .env.example .env
nano .env
```

Set `DATA_PATH` (the folder for settings, uploads and `photos/`, e.g. `/volume1/docker/home-portal` on a Synology NAS) and `TZ` (your timezone). Save with `Ctrl+O`, then `Enter`, then exit with `Ctrl+X`.

### 5. Build and start Home Portal

```bash
docker compose up -d --build
```

### 6. Open the portal

Go to `http://YOUR-HOST` in your browser, replacing `YOUR-HOST` with the IP address or hostname of the machine running Docker.

---

## macOS

### 1. Open a terminal

Press `Cmd+Space`, type `Terminal`, press Enter.

### 2. Check whether Docker is installed

```bash
docker --version
docker compose version
```

- Version numbers shown → continue to step 3.
- `command not found` → install **Docker Desktop for Mac** from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) (choose Apple Silicon or Intel), drag it to Applications, launch it, and wait for the whale icon in the menu bar to show it's running. Then re-run the commands above.

### 3. Download Home Portal

No-Git route: download the ZIP from [github.com/9t29zhmwdh-coder/HomePortal](https://github.com/9t29zhmwdh-coder/HomePortal) (green **Code** button → **Download ZIP**) and extract it (double-click in Finder).

Or, with Git:

```bash
git clone https://github.com/9t29zhmwdh-coder/HomePortal.git
cd HomePortal
```

### 4. Create and edit your configuration file

```bash
cp .env.example .env
nano .env
```

Set `DATA_PATH` and `TZ`. Save with `Ctrl+O`, `Enter`, exit with `Ctrl+X`.

### 5. Build and start Home Portal

```bash
docker compose up -d --build
```

### 6. Open the portal

Go to `http://localhost` in your browser.

---

## What you should see

After `docker compose up -d --build` finishes, two containers run in the background: the FastAPI app and an Nginx reverse proxy in front of it. Opening the portal address in your browser shows the Home Portal page. On the very first start it has no links yet and says so.

## Set a password and add your tiles

1. Click the gear icon at the top right. Home Portal asks for an admin password (at least 10 characters). Do this right away: whoever sets it first can change the portal.
2. You land in the settings. Under **Appearance**, pick a theme, a background, a font and the language, then **Save**. To use your own picture as background, choose it under **Upload an image**.
3. Click **Back to the portal**, then the pencil icon next to the gear. This is the edit mode for the current tab.
4. Under **New tile**, choose **Link** and click **Add**. Enter a name and an address starting with `http://` or `https://`, optionally a description and an emoji, and save. Repeat for your other services.
5. Drag tiles by their ⠿ handle to where you want them, pick sizes from the list on each tile, and click **Save layout**, then **Done**.

More tabs (for example "Media" or "Technology") are added in the settings under **Tabs**.

To show values from Home Assistant, open the settings, **Connections**, enter the Home Assistant address and a long-lived access token (Home Assistant: your profile, **Security**, **Long-lived access tokens**, **Create token**), and click **Save and test**. Then add a **Home Assistant** tile and enter the entity ids, one per line, as listed in Home Assistant under **Settings**, **Devices & services**, **Entities**.

For the album, copy photos into the `photos` folder inside your `DATA_PATH` folder (create it if it is not there), then reload the page.

Anyone on your network can open the page without a password. To change that, tick **Ask for the password to view the portal, too** under **Access**.

To check what's happening behind the scenes:

```bash
docker compose logs -f app
```

Press `Ctrl+C` to stop following the logs (this does not stop the app).

To stop Home Portal later:

```bash
docker compose down
```

To apply changes after editing `.env` or updating the code:

```bash
docker compose up -d --build
```

---

### Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `'docker' is not recognized...` (Windows) or `command not found: docker` (Linux/macOS) | Docker isn't installed, or the terminal was opened before installing it | Install Docker (see steps above), then open a **new** terminal window |
| "Cannot connect to the Docker daemon" | Docker Desktop / the Docker service isn't running | Windows/macOS: open Docker Desktop and wait for it to say "running". Linux: `sudo systemctl start docker` |
| Windows: error mentioning WSL2 when starting Docker Desktop | WSL2 missing or outdated | Open PowerShell as Administrator, run `wsl --install`, then restart your computer |
| Browser shows "connection refused" at `http://localhost` or `http://YOUR-HOST` | Containers still starting, or wrong host/IP used | Wait a minute and retry; run `docker compose logs -f app` to check for errors; confirm you're using the correct IP if running on a NAS/remote server |
| A link tile is refused as not valid | It does not start with `http://` or `https://` | Write the full address, e.g. `http://192.168.1.10:5000` |
| "Too many attempts" at login | Five wrong passwords within five minutes | Wait five minutes |
| Forgot the admin password | Only its hash is stored | Stop the container, delete `auth.json` in `DATA_PATH`, start again and set a new password; links and settings stay |
| Photos do not show | Wrong folder or format | They must be in `DATA_PATH/photos/` as `.jpg`, `.png`, `.webp` or `.gif` |
| "Layout not saved (layout_overlap)" | Two tiles would sit on the same cells | Move one of them, then save again |
| Home Assistant tile says the token was refused | Token revoked or mistyped | Create a new long-lived token in Home Assistant and save it under **Connections** |
| Home Assistant tile says Home Assistant does not answer | Wrong address, or the portal server cannot reach it | Open the address from the NAS or server that runs Home Portal; use the IP address rather than a `.local` name |
| Leaving the edit mode asks whether to leave the page | The layout has unsaved changes | Click **Save layout** first |
