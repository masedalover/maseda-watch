
import os, re, time, unicodedata, urllib.parse, urllib.request

URL = "https://store.maseda-art.com/products/the-one-only"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
STATE = "state.txt"
LOOP_SECONDS = int(os.environ.get("LOOP_SECONDS", "0"))  # 0 = una sola comprobación
INTERVAL = int(os.environ.get("INTERVAL", "20"))  # segundos entre comprobaciones


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def norm(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


def current_status():
    try:
        html = get(URL)
    except Exception as e:
        print("No pude leer la web:", e)
        return None

    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = m.group(1).strip() if m else ""
    buttons = re.findall(r'<button[^>]*name="add"[^>]*>', html, re.I | re.S)
    can_buy = any("disabled" not in b.lower() for b in buttons)

    if can_buy:
        status = "DISPONIBLE"
    elif title and "PROXIMAMENTE" not in norm(title):
        status = "CAMBIO"
    else:
        status = "ESPERANDO"
    print(time.strftime("%H:%M:%S"), "|", title, "| botones:", len(buttons), "|", status, flush=True)
    return status


def notify(msg):
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=msg.encode("utf-8"),
            headers={"Title": "Maseda - THE ONE", "Priority": "urgent", "Click": URL, "Tags": "dollar"},
        )
        urllib.request.urlopen(req, timeout=20)
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        q = urllib.parse.urlencode({"chat_id": chat, "text": f"{msg}\n{URL}"})
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage?{q}", timeout=20)


def main():
    prev = open(STATE).read().strip() if os.path.exists(STATE) else ""
    end = time.time() + LOOP_SECONDS
    while True:
        status = current_status()
        if status and status != prev:
            try:
                if status == "DISPONIBLE":
                    notify("¡THE ONE está DISPONIBLE ahora mismo! Corre.")
                elif status == "CAMBIO":
                    notify("La ficha de THE ONE ha cambiado (ya no pone próximamente). Míralo.")
            except Exception as e:
                print("Fallo al avisar:", e)
            prev = status
            open(STATE, "w").write(status)
        if time.time() + INTERVAL >= end:
            break
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
