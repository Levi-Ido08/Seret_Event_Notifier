import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = 'https://www.seret.co.il/extras/seretspecials.asp'
BASE_URL = 'https://www.seret.co.il'
CACHE_FILE = 'seret_cache.json'

SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'levido08@gmail.com').strip()
IDO_APP_PASSWORD = os.getenv('IDO_APP_PASSWORD', '').strip()
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL', 'levi0080@gmail.com').strip()

def send_email(new_items):
    msg = MIMEMultipart()
    msg['Subject'] = 'עדכון חדש: אתר סרט'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    body = '<div dir="rtl" style="text-align: right; font-family: Arial, sans-serif;">'
    body += 'נמצאו עדכונים חדשים::<br><br>'

    for item in new_items:
        body += f"כותרת/טקסט: {item['title']}<br>"
        body += f"לינק: {item['link']}<br><br>"
        body += '-' * 30 + '<br>'

    body += '</div>'

    msg.attach(MIMEText(body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, IDO_APP_PASSWORD)
            server.send_message(msg)
        print('המייל נשלח בהצלחה!')
    except Exception as e:
        print(f'שגיאה בשליחת המייל: {e}')

def get_events_list():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until='domcontentloaded')
        html_content = page.content()
        browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    main_content = soup.find('div', id='maincontent')
    
    items = []
    if main_content:
        links = main_content.find_all('a', href=True)
        for link_tag in links:
            link = link_tag['href']
            if not link.startswith('http'):
                link = BASE_URL + '/' + link.lstrip('/')

            title = link_tag.get_text(strip=True)
            if not title:
                title = link

            items.append({
                'title': title,
                'link': link,
            })

    return items


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_cache(events):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)


def main():
    print('Checking for Seret updates...')
    current_items = get_events_list()
    cached_items = load_cache()

    cached_links = {e['link'] for e in cached_items}
    new_items = [e for e in current_items if e['link'] not in cached_links]

    if new_items:
        print(f'>>> Found {len(new_items)} new updates! <<<')
        for item in new_items:
            print(f"Title: {item['title']}")
            print(f"Link: {item['link']}\n")

        send_email(new_items)
        save_cache(current_items)
    else:
        print('No New Updates Found.')


if __name__ == '__main__':
    main()