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
5. On the `SECRET` line, replace `change-me-to-something-only-you-know` with your own password-like word. Save (💾).
6. **Deploy → New deployment** → gear ⚙ → **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
   - **Deploy** → **Authorize access** → choose your account → *Advanced* → *Go to project (unsafe)* → **Allow**.
     (It says "unsafe" only because you wrote the script yourself and Google hasn't reviewed it.)
7. Copy the **Web app URL** (ends in `/exec`).

### B. Turn on the free web page (one time, on GitHub)
1. Open the repo on GitHub → **Settings → Pages**.
2. Source: **Deploy from a branch** → Branch: `claude/ai-old-devices-projects-2wu7gm`, folder **/(root)** → **Save**.
3. After ~1 minute the page is live at **https://arpangpta.github.io/Mobilecheck/**

### C. Start the old phone
1. Make a link like this (put your values in):
   ```
   https://arpangpta.github.io/Mobilecheck/?endpoint=PASTE_WEB_APP_URL&key=YOUR_SECRET&room=bedroom
   ```
   Send it to yourself (Gmail / Google Keep / WhatsApp) and open it on the old phone **in Chrome**.
   (Or open the plain page and type the values into **Settings**.)
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
