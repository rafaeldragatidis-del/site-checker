import os
import socket
import ssl
import sys
import urllib.parse
import requests


def check_ssl(url):
    """1. Έλεγχος αν το SSL πιστοποιητικό είναι έγκυρο και ενεργό."""
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.hostname
    port = parsed_url.port or 443

    if parsed_url.scheme != "https":
        return "❌ ⚠️ Μη ασφαλές πρωτόκολλο (HTTP αντί για HTTPS)"

    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                ssock.getpeercert()
                return "✅ Έγκυρο"
    except ssl.SSLCertVerificationError as e:
        return f"❌ Άκυρο Πιστοποιητικό (Σφάλμα Επαλήθευσης: {e.reason})"
    except Exception as e:
        return f"❌ Αποτυχία σύνδεσης / Έλεγχου SSL ({str(e)})"


def check_security_headers(url):
    """2. Έλεγχος αν το X-Frame-Options header είναι ρυθμισμένο."""
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        headers = response.headers
        x_frame_options = headers.get("X-Frame-Options")

        if x_frame_options:
            val = x_frame_options.upper()
            if val in ["DENY", "SAMEORIGIN"]:
                return f"✅ Ρυθμισμένο σωστά ({x_frame_options})"
            return f"⚠️ Υπάρχει αλλά με μη τυπική τιμή ({x_frame_options})"
        else:
            return "❌ Λείπει (Κίνδυνος για Clickjacking)"
    except requests.exceptions.RequestException:
        return "❌ Αποτυχία HTTP αίτησης κατά τον έλεγχο headers"


def check_robots_txt(url):
    """3. Έλεγχος αν υπάρχει το αρχείο robots.txt."""
    parsed_url = urllib.parse.urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    try:
        response = requests.get(robots_url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return "✅ Βρέθηκε"
        else:
            return f"❌ Δεν βρέθηκε (Status Code: {response.status_code})"
    except requests.exceptions.RequestException:
        return "❌ Αποτυχία σύνδεσης στο robots.txt"


def send_telegram_alert(token, chat_id, message):
    """Αποστολή ειδοποίησης στο Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Αποτυχία αποστολής Telegram: {e}")


def main():
    # Διάβασμα των ρυθμίσεων από το περιβάλλον του GitHub
    urls_env = os.getenv("URLS_TO_CHECK", "")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not urls_env:
        print(
            "❌ Σφάλμα: Δεν βρέθηκαν URLs για έλεγχο. Ρύθμισε το 'URLS_TO_CHECK' στα Secrets."
        )
        sys.exit(1)

    # Διαχωρισμός των URLs αν είναι πολλά (χωρισμένα με κόμμα)
    urls_to_check = [url.strip() for url in urls_env.split(",") if url.strip()]

    has_errors = False
    report_lines = ["🚨 Αναφορά Προβλημάτων Ιστοσελίδων:"]

    for url in urls_to_check:
        print(f"Έλεγχος: {url}...")
        ssl_res = check_ssl(url)
        headers_res = check_security_headers(url)
        robots_res = check_robots_txt(url)

        # Αν βρεθεί σφάλμα (❌), το καταγράφουμε
        if "❌" in ssl_res or "❌" in headers_res or "❌" in robots_res:
            has_errors = True
            report_lines.append(
                f"\n🔗 Site: {url}\n"
                f"🔒 SSL: {ssl_res}\n"
                f"🛡️ Header: {headers_res}\n"
                f"🤖 Robots: {robots_res}\n"
                f"------------------------"
            )

    # Αν βρέθηκαν σφάλματα και έχουμε ρυθμίσει Telegram, στείλε μήνυμα
    if has_errors:
        full_message = "\n".join(report_lines)
        print("\n" + full_message)

        if telegram_token and telegram_chat_id:
            send_telegram_alert(telegram_token, telegram_chat_id, full_message)
            print("📬 Η ειδοποίηση στάλθηκε στο Telegram.")
        else:
            print(
                "⚠️ Το Telegram δεν έχει ρυθμιστεί, η αναφορά τυπώθηκε μόνο στα logs."
            )
    else:
        print("\n✅ Όλα τα sites είναι πεντακάθαρα! Κανένα πρόβλημα.")


if __name__ == "__main__":
    main()
