#!/usr/bin/env python3
"""Room Sensor for Termux: reads the phone's real sensors and sends one row
per minute to the same Google Sheet as the web page.

Commands (via the `room-sensor` shortcut):
  run      - run in the foreground (start/stop use this in the background)
  check    - show one reading of each sensor
  test     - send a test row and print the sheet's reply
"""
import json, os, random, string, subprocess, sys, threading, time, urllib.request
from datetime import datetime

HOME = os.path.expanduser("~/.room-sensor")
CONF = os.path.join(HOME, "config.json")
QUEUE = os.path.join(HOME, "queue.json")
MOVE_SENSOR = "Linear Acceleration"
LIGHT_SENSOR = "stk3x1x alsprx"
SAMPLE_MS = 200            # 5 readings per second
MOVE_THRESHOLD = 0.3       # m/s^2 of linear acceleration that counts as movement
ROW_EVERY = 60             # seconds
BATTERY_EVERY = 15         # seconds


def log(msg):
    print(datetime.now().strftime("%H:%M:%S"), msg, flush=True)


# ---------------- config & queue ----------------
def load_conf():
    os.makedirs(HOME, exist_ok=True)
    try:
        with open(CONF) as f:
            c = json.load(f)
    except Exception:
        c = {}
    c.setdefault("endpoint", "")
    c.setdefault("room", "room")
    c.setdefault("light_index", 0)
    if not c.get("key"):
        c["key"] = "t" + "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(22))
    save_conf(c)
    return c


def save_conf(c):
    os.makedirs(HOME, exist_ok=True)
    with open(CONF, "w") as f:
        json.dump(c, f, indent=1)


qlock = threading.Lock()


def load_queue():
    try:
        with open(QUEUE) as f:
            return json.load(f)
    except Exception:
        return []


def save_queue(q):
    q = q[-5000:]
    tmp = QUEUE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(q, f)
    os.replace(tmp, QUEUE)


def enqueue(row):
    with qlock:
        q = load_queue()
        q.append(row)
        save_queue(q)


# ---------------- sending ----------------
def post(conf, rows):
    """Returns (ok, message). Apps Script answers POST with a redirect; urllib
    follows it with a GET, which is what Google expects."""
    body = json.dumps({"key": conf["key"], "rows": rows}).encode()
    req = urllib.request.Request(conf["endpoint"], data=body, method="POST",
                                 headers={"Content-Type": "text/plain;charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode("utf-8", "replace")
    except Exception as e:
        return False, "could not reach the sheet (%s)" % e
    try:
        reply = json.loads(txt)
    except Exception:
        return False, "sheet sent an error page: " + " ".join(txt.split())[:200]
    if reply.get("ok"):
        return True, "added %s rows" % reply.get("added")
    return False, "sheet says: %s" % reply.get("error")


def flush(conf):
    if not conf["endpoint"]:
        return
    while True:
        with qlock:
            batch = load_queue()[:200]
        if not batch:
            return
        ok, msg = post(conf, batch)
        if not ok:
            log("Send failed, will retry: " + msg)
            if "wrong key" in msg:
                log("The sheet is locked to another phone. In Apps Script open Project Settings > "
                    "Script properties, delete PHONE_KEY, then this phone will be accepted.")
            return
        with qlock:
            save_queue(load_queue()[len(batch):])
        log("Sent %d row(s)." % len(batch))


# ---------------- sensors ----------------
def termux_json(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
        return json.loads(out)
    except Exception:
        return None


def battery():
    b = termux_json(["termux-battery-status"]) or {}
    plugged = b.get("plugged", "")
    charging = None if not plugged else (plugged != "UNPLUGGED")
    return b.get("percentage"), charging


def parse_reading(pairs):
    """pairs: list of (sensor name, data) from one termux-sensor JSON object.
    The light chip appears twice under the same name (light + proximity)."""
    move = None
    alsprx = []
    for name, data in pairs:
        if isinstance(data, list):          # nested objects also arrive as (key, value) pairs
            data = dict(data)
        vals = data.get("values") if isinstance(data, dict) else None
        if not vals:
            continue
        if name.startswith(MOVE_SENSOR) and move is None:
            x, y, z = (list(vals) + [0, 0, 0])[:3]
            move = (x * x + y * y + z * z) ** 0.5
        elif name.startswith(LIGHT_SENSOR):
            alsprx.append(vals[0])
    return move, alsprx


def sensor_stream(on_reading, stop):
    """Runs termux-sensor continuously and calls on_reading(move, alsprx)."""
    dec = json.JSONDecoder(object_pairs_hook=lambda p: p)
    while not stop.is_set():
        subprocess.run(["termux-sensor", "-c"], capture_output=True)
        p = subprocess.Popen(["termux-sensor", "-s", MOVE_SENSOR + "," + LIGHT_SENSOR, "-d", str(SAMPLE_MS)],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        buf = ""
        try:
            for line in p.stdout:
                if stop.is_set():
                    break
                buf += line
                while True:
                    s = buf.lstrip()
                    if not s:
                        buf = ""
                        break
                    try:
                        obj, end = dec.raw_decode(s)
                    except ValueError:
                        break
                    buf = s[end:]
                    if obj:
                        on_reading(*parse_reading(obj))
        finally:
            p.kill()
            subprocess.run(["termux-sensor", "-c"], capture_output=True)
        if not stop.is_set():
            log("Sensor stream stopped; restarting in 5 s.")
            time.sleep(5)


# ---------------- main loop ----------------
class Acc:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.sec_vals = {}       # second -> max movement in that second
        self.light_sum = 0.0
        self.light_n = 0


def stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_row(conf, acc, event, batt):
    with acc.lock:
        secs = list(acc.sec_vals.values())
        light = round(acc.light_sum / acc.light_n) if acc.light_n else ""
        acc.reset()
    pct, charging = batt
    return {
        "time": stamp(), "room": conf["room"], "event": event,
        "motion_avg": round(sum(secs) / len(secs), 2) if secs else "",
        "motion_max": round(max(secs), 2) if secs else "",
        "moving_secs": sum(1 for v in secs if v > MOVE_THRESHOLD) if secs else "",
        "noise_avg": "", "noise_max": "",
        "light": light,
        "battery": "" if pct is None else pct,
        "charging": "" if charging is None else ("yes" if charging else "no"),
    }


def run(conf):
    if not conf["endpoint"]:
        sys.exit("No sheet URL yet. Run:  room-sensor url https://script.google.com/.../exec")
    acc = Acc()
    li = int(conf.get("light_index", 0))

    def on_reading(move, alsprx):
        with acc.lock:
            if move is not None:
                sec = int(time.time())
                acc.sec_vals[sec] = max(acc.sec_vals.get(sec, 0.0), move)
            if len(alsprx) > li:
                acc.light_sum += alsprx[li]
                acc.light_n += 1

    stop = threading.Event()
    threading.Thread(target=sensor_stream, args=(on_reading, stop), daemon=True).start()
    batt = battery()
    log("Room sensor started (room: %s). Battery %s%%, charging: %s" % (conf["room"], batt[0], batt[1]))
    enqueue(make_row(conf, acc, "started", batt))
    flush(conf)
    next_row = time.time() + ROW_EVERY
    try:
        while True:
            time.sleep(BATTERY_EVERY)
            new = battery()
            if new[1] is not None and batt[1] is not None and new[1] != batt[1]:
                ev = "power_back" if new[1] else "power_cut"
                log("Power cut / charger removed!" if ev == "power_cut" else "Power is back.")
                enqueue(make_row(conf, acc, ev, new))
                flush(conf)
            batt = new
            if time.time() >= next_row:
                next_row += ROW_EVERY
                enqueue(make_row(conf, acc, "reading", batt))
                flush(conf)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        subprocess.run(["termux-sensor", "-c"], capture_output=True)
        log("Stopped.")


def check(conf):
    print("Reading sensors (5 s)...")
    out = subprocess.run(["termux-sensor", "-s", MOVE_SENSOR + "," + LIGHT_SENSOR, "-n", "3", "-d", "1000"],
                         capture_output=True, text=True, timeout=60).stdout
    subprocess.run(["termux-sensor", "-c"], capture_output=True)
    dec = json.JSONDecoder(object_pairs_hook=lambda p: p)
    s, last = out.strip(), None
    while s:
        try:
            obj, end = dec.raw_decode(s)
        except ValueError:
            break
        if obj:
            last = obj
        s = s[end:].lstrip()
    if not last:
        print("No sensor data. Is the Termux:API app installed and allowed to run?")
        return
    move, alsprx = parse_reading(last)
    li = int(conf.get("light_index", 0))
    print("Movement: %s" % (None if move is None else round(move, 3)))
    for i, v in enumerate(alsprx):
        print("Light chip value %d: %s%s" % (i, v, "   <- used as LIGHT" if i == li else ""))
    pct, ch = battery()
    print("Battery: %s%%  charging: %s" % (pct, ch))
    print("\nTip: cover the top of the phone (near the earpiece) and run check again.\n"
          "The LIGHT value should drop. If the other one drops instead, run:  room-sensor swap-light")


def test(conf):
    if not conf["endpoint"]:
        sys.exit("No sheet URL yet. Run:  room-sensor url https://script.google.com/.../exec")
    row = make_row(conf, Acc(), "test", battery())
    ok, msg = post(conf, [row])
    print(("OK - " if ok else "PROBLEM - ") + msg)
    if not ok and "wrong key" in msg:
        print("The sheet is locked to another phone. In Apps Script: Project Settings > Script properties >"
              " delete PHONE_KEY, then run  room-sensor test  again.")


if __name__ == "__main__":
    c = load_conf()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    fn = {"run": run, "check": check, "test": test}.get(cmd)
    if fn:
        fn(c)
