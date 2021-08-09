import os
import urllib.parse
from datetime import date, datetime, timedelta, timezone
import json
import requests
from dotenv import load_dotenv

load_dotenv()
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
ORGANIZATION_ID = os.getenv('ORGANIZATION_ID')
LOGIN_URL= os.getenv('LOGIN_URL')
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIMEZONE = timezone(offset=timedelta(hours=9))

def create_line_message(text):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(LINE_ACCESS_TOKEN)
    }
    data = {
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }
    requests.post(url, data=json.dumps(data), headers=headers)

def fetch_available_time_slot():
    base_url = 'https://api-cache.vaccines.sciseed.jp/'
    url = urllib.parse.urljoin(base_url, 'public/{}/reservation_frame'.format(ORGANIZATION_ID))
    now = datetime.now(tz=TIMEZONE)
    date_to = now + timedelta(days=30)
    payload = {
        'item_id': '3',
        'start_date_after': date(now.year, now.month, now.day).strftime('%Y-%m-%d'),
        'start_date_before': date(date_to.year, date_to.month, date_to.day).strftime('%Y-%m-%d')
    }
    res = requests.get(url, params=payload)
    time_slots = res.json()['reservation_frame']
    return [t for t in time_slots if is_time_slot_available(t)]

def is_time_slot_available(t):
    now = datetime.now(tz=TIMEZONE)
    t_time = datetime.strptime(t['start_at'], '%Y-%m-%dT%H:%M:%S%z')
    if t['is_published'] and t['reservation_cnt'] < t['reservation_cnt_limit'] and now < t_time:
        return True
    else:
        return False

def display_format_time_slot(t):
    d = t['start_at'][:10].replace('-', '/')
    start_time = t['start_at'][11:16]
    end_time = t['end_at'][11:16]
    next_d = t['next']['start_at'][:10].replace('-', '/')
    next_start_time = t['next']['start_at'][11:16]
    next_end_time = t['next']['end_at'][11:16]
    ret = '\n------\n'
    ret += '日時: {} {}-{}\n'.format(d, start_time, end_time)
    ret += '会場: {}\n'.format(t['name'])
    ret += '空き: {}件 (最大: {}件)\n'.format((t['reservation_cnt_limit'] - t['reservation_cnt']), t['reservation_cnt_limit'])
    ret += '(2回目予定: {} {}-{})'.format(next_d, next_start_time, next_end_time)
    return ret

def did_notify_recently():
    dir = os.path.dirname(__file__)
    log_file_path = os.path.join(dir, 'last_notified.log')
    if not os.path.isfile(log_file_path):
        return False
    with open(log_file_path, mode='r') as f:
        s = f.read()
    last_notified = datetime.strptime(s, DATETIME_FORMAT)
    now = datetime.now()
    if now - last_notified < timedelta(hours=1):
        return True
    else:
        return False

def save_last_notified():
    dir = os.path.dirname(__file__)
    log_file_path = os.path.join(dir, 'last_notified.log')
    with open(log_file_path, mode='w') as f:
        now = datetime.now()
        f.write(now.strftime(DATETIME_FORMAT))

if __name__ == '__main__':
    if did_notify_recently():
        exit()
    available_time_slot = fetch_available_time_slot()
    if len(available_time_slot) == 0:
        print('No time slot avaliable.')
        exit()
    message = 'ワクチン接種予約に空きがあるようですよ。\n{}'.format(LOGIN_URL)
    for t in available_time_slot:
        message += display_format_time_slot(t)
    create_line_message(message)
    save_last_notified()
