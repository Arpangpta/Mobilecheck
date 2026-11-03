# Room Sensor (old phone → Google Sheet)

Turns an old Android phone into a room sensor using **only its web browser**.
No apps to install, no laptop, no Raspberry Pi, ₹0.

Every minute the phone records:

| Column | Meaning |
|---|---|
| `motion_avg`, `motion_max`, `moving_secs` | How much the phone/table shook, and how many seconds of that minute had movement |
| `noise_avg`, `noise_max` | Loudness 0–100 (only the volume level; no sound is recorded or sent) |
| `light` | Rough brightness from the camera, 0–255 (optional, off by default) |
| `battery`, `charging` | Battery % and whether it is on the charger |
| `event` | `reading`, `started`, `test`, `power_cut`, `power_back` |

```
Old phone (Chrome, this page open)  ──every minute──▶  Google Apps Script  ──▶  Google Sheet
```

Files:
- `index.html` – the sensor page (served free by GitHub Pages)
- `apps-script/Code.gs` – the receiver you paste into your Google Sheet

---

## Setup (all on phones)

### A. Make the Google Sheet receiver (do this on your main phone)
1. In Chrome open **sheets.new** (signed in to Google). Name the sheet "Room Sensor".
2. Chrome menu ⋮ → tick **Desktop site** (the script editor needs it).
3. In the sheet: **Extensions → Apps Script**.
4. Delete what's there and paste everything from [`apps-script/Code.gs`](apps-script/Code.gs).
5. Save (💾). Nothing to edit – it works as pasted.
6. **Deploy → New deployment** → gear ⚙ → **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
   - **Deploy** → **Authorize access** → choose your account → *Advanced* → *Go to project (unsafe)* → **Allow**.
     (It says "unsafe" only because you wrote the script yourself and Google hasn't reviewed it.)
7. Copy the **Web app URL** (ends in `/exec`).

### B. Turn on the free web page (one time, on GitHub)
1. Open the repo on GitHub → **Settings → Pages**.
2. Source: **Deploy from a branch** → Branch: `room-sensor`, folder **/(root)** → **Save**.
3. After ~1 minute the page is live at **https://arpangpta.github.io/Mobilecheck/**

### C. Start the old phone
1. Make a link like this (put your values in):
   ```
   https://arpangpta.github.io/Mobilecheck/?endpoint=PASTE_WEB_APP_URL&room=bedroom
   ```
   Send it to yourself (Gmail / Google Keep / WhatsApp) and open it on the old phone **in Chrome**.
   (Or open the plain page and paste the URL into **Settings**. The secret key is created automatically.)
2. Tap **Send test row** → a row should appear in the sheet's **Readings** tab within a few seconds.
3. Tap **▶ Start sensing** and **Allow** microphone (and camera if you turned on Light).
4. Phone settings so it keeps running:
   - **Settings → Lock screen → Sleep → Never** (screen must stay on; the page pauses if the screen turns off or you switch apps).
   - Keep it **plugged in**, on a hard surface, not on the bed.
   - Tap **Dim screen** to make it black (tap again to wake).

If the internet drops, rows wait on the phone and are sent later.

### D. Get insights
Open the sheet anytime, or **File → Download → CSV** and give it to Claude Code:
"what happened in my room this week?"

---

## Option 2: Termux version (better – real light sensor, runs with screen off)

Needs the **Termux** and **Termux:API** apps, both from F-Droid. It sends the same columns to the same
Google Sheet (noise is left empty in this version).

In Termux:
```
curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/termux/install.sh | bash
room-sensor url        (after copying your /exec URL on this phone)
room-sensor test
room-sensor start
```

| Command | What it does |
|---|---|
| `room-sensor test` | sends one test row and prints the sheet's reply |
| `room-sensor check` | shows movement, light and battery right now |
| `room-sensor start` / `stop` | start / stop sensing in the background |
| `room-sensor status` | is it running + recent log |
| `room-sensor room bedroom` | set the room name |
| `room-sensor find-light` | detects which sensor is the real light sensor (run with the room light on) |
| `room-sensor update` | get the latest version |

If `test` says **wrong key**: the sheet is locked to the phone that sent first. In Apps Script open
**Project Settings → Script properties**, delete `PHONE_KEY`, and run `room-sensor test` again.

Keep Termux alive on MIUI: Settings → Apps → Termux → Autostart **on**, Battery saver **No restrictions**,
and lock Termux in the recent-apps screen.

---

# Phone Server – host websites on the old phone

nginx serves your sites on the phone, and a free **Cloudflare quick tunnel** gives them a public
`https://….trycloudflare.com` address (no router setup, works behind Jio/Airtel CGNAT).
Sites are pulled from GitHub, so you never need a laptop on the phone.

Install in Termux:
```
curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/server/install.sh | bash
phone-server start
```
The portfolio in [`sites/portfolio/`](sites/portfolio/) is installed as the home page.
It shows a live "served from a 2017 Redmi Y1" line (battery, uptime, temperature) from `/status.json`.

| Command | What it does |
|---|---|
| `phone-server start` | start nginx + tunnel, prints the public address |
| `phone-server url` | show and copy the public address |
| `phone-server status` | what is running, which sites |
| `phone-server add NAME REPO_URL [BRANCH] [FOLDER]` | host a site from a public GitHub repo at `/NAME/` |
| `phone-server home NAME` | make a site the home page `/` |
| `phone-server update` | pull the latest version of all sites (also automatic every 15 minutes) |
| `phone-server remove NAME` / `stop` / `restart` / `log` / `self-update` | |

### React / Angular sites
They are built into static files, then committed (e.g. a `dist/` folder) to a GitHub repo.
Set the base path to `/NAME/` when building:
- **Vite (React):** `base: '/NAME/'` in `vite.config.js`
- **Create React App:** `"homepage": "/NAME/"` in `package.json`
- **Angular:** `ng build --base-href /NAME/`

Then: `phone-server add NAME https://github.com/Arpangpta/REPO.git main dist`.
Page refreshes on inner routes work (nginx falls back to the app's `index.html`).

**Notes:** the free address changes whenever the tunnel restarts – check it with `phone-server url`.
For a permanent address, use your own domain with a named Cloudflare tunnel.
