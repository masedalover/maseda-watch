import json, os, sys, urllib.request, urllib.parse

URL = "https://store.maseda-art.com/products/the-one-only"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
STATE = "state.txt"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def current_status():
    # 1) JSON de Shopify: dice si hay stock
    try:
        data = json.loads(get(URL + ".js"))
        if data.get("available"):
            return "DISPONIBLE"
        title = data.get("title", "")
    except Exception as e:
        print("No pude leer el JSON:", e)
        title = ""
    # 2) Si ya no pone PRÓXIMAMENTE en el título, algo ha cambiado
    if not title:
        try:
            html = get(URL)
            if "<title>" in html:
                title = html.split("<title>")[1].split("</title>")[0]
        except Exception as e:
            print("No pude leer la web:", e)
            sys.exit(0)
    if title and "PRÓXIMAMENTE" not in title.upper() and "PROXIMAMENTE" not in title.upper():
        return "CAMBIO"
    return "ESPERANDO"


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
    status = current_status()
    prev = open(STATE).read().strip() if os.path.exists(STATE) else ""
    print("Estado:", status, "| anterior:", prev or "-")
    if status != prev:
        if status == "DISPONIBLE":
            notify("¡THE ONE está DISPONIBLE ahora mismo! Corre.")
        elif status == "CAMBIO":
            notify("La ficha de THE ONE ha cambiado (ya no pone próximamente). Míralo.")
        open(STATE, "w").write(status)


if __name__ == "__main__":
    main()
