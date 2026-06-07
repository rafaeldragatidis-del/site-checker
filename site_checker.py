import os
import socket
import ssl
import sys
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


def check_ssl(url):
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.hostname
    port = parsed_url.port or 443
    if parsed_url.scheme != "https":
        return "❌ Μη ασφαλές πρωτόκολλο (HTTP αντί για HTTPS)"
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                ssock.getpeercert()
                return "✅ Έγκυρο"
    except Exception:
        return "❌ Πρόβλημα με το πιστοποιητικό SSL (Ληγμένο ή Άκυρο)"


def check_security_headers(url):
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        if "X-Frame-Options" in response.headers:
            return "✅ Ρυθμισμένο σωστά"
        return "❌ Λείπει το X-Frame-Options header (Κίνδυνος Clickjacking)"
    except Exception:
        return "❌ Αποτυχία σύνδεσης για έλεγχο Headers"


def check_robots_txt(url):
    parsed_url = urllib.parse.urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return "✅ Βρέθηκε"
        return f"❌ Λείπει το αρχείο robots.txt (Πρόβλημα SEO)"
    except Exception:
        return "❌ Αποτυχία σύνδεσης στο robots.txt"


def send_auto_email(sender_email, sender_password, target_email, site_url, errors_text):
    """Λειτουργία που στέλνει αυτόματα το προσωποποιημένο email."""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target_email
    msg['Subject'] = f"Σημαντικό: Θέματα ασφαλείας και SEO στην ιστοσελίδα {site_url}"

    body = f"""Καλημέρα σας,

Ονομάζομαι Ραφαήλ και διεξήγαγα έναν αυτόματο έλεγχο ασφαλείας και βελτιστοποίησης στην ιστοσελίδα σας ({site_url}).

Εντοπίστηκαν ορισμένα τεχνικά ζητήματα που χρήζουν άμεσης προσοχής:
{errors_text}

Αυτά τα προβλήματα μπορούν να επηρεάσουν την εμπιστοσύνη των επισκεπτών σας αλλά και τη θέση της σελίδας σας στη Google. Μπορώ να αναλάβω την άμεση διόρθωσή τους με ένα πολύ χαμηλό κόστος.

Αν σας ενδιαφέρει να το φτιάξουμε, απαντήστε μου σε αυτό το email για να συζητήσουμε τις λεπτομέρειες.

Με εκτίμηση,
Ραφαήλ Δραγατίδης"""

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()
        print(f"📬 Το email στάλθηκε επιτυχώς στο {target_email}!")
    except Exception as e:
        print(f"❌ Αποτυχία αποστολής email: {e}")


def main():
    urls_env = os.getenv("URLS_TO_CHECK", "")
    my_email = os.getenv("MY_EMAIL")
    my_password = os.getenv("MY_GMAIL_APP_PASSWORD")
    client_email = os.getenv("CLIENT_EMAIL") # Το email του ιδιοκτήτη που θα λάβει την προσφορά

    if not urls_env:
        print("❌ Δεν βρέθηκαν URLs.")
        sys.exit(1)

    urls_to_check = [url.strip() for url in urls_env.split(",") if url.strip()]

    for url in urls_to_check:
        print(f"Έλεγχος για το site: {url}...")
        ssl_res = check_ssl(url)
        headers_res = check_security_headers(url)
        robots_res = check_robots_txt(url)

        # Αν βρεθεί έστω και ένα σφάλμα (❌)
        if "❌" in ssl_res or "❌" in headers_res or "❌" in robots_res:
            errors_list = []
            if "❌" in ssl_res: errors_list.append(f"- {ssl_res}")
            if "❌" in headers_res: errors_list.append(f"- {headers_res}")
            if "❌" in robots_res: errors_list.append(f"- {robots_res}")
            
            errors_str = "\n".join(errors_list)
            
            # Αν έχουμε ρυθμίσει email, στείλτο αυτόματα στον πελάτη!
            if my_email and my_password and client_email:
                send_auto_email(my_email, my_password, client_email, url, errors_str)
            else:
                print(f"⚠️ Βρέθηκαν σφάλματα για το {url} αλλά δεν έχουν ρυθμιστεί τα email στα Secrets.")
        else:
            print(f"✅ Το site {url} είναι καθαρό. Δεν στάλθηκε email.")


if __name__ == "__main__":
    main()
