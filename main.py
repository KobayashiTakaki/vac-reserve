import os
import urllib.parse
from datetime import date
import json
import requests
from dotenv import load_dotenv

load_dotenv()
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
ORGANIZATION_ID = os.getenv('ORGANIZATION_ID')
LOGIN_URL= os.getenv('LOGIN_URL')

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

def fetch_time_slots():
    base_url = 'https://api-cache.vaccines.sciseed.jp/'
    url = urllib.parse.urljoin(base_url, 'public/{}/reservation_frame'.format(ORGANIZATION_ID))
    payload = {
        'item_id': '3',
        'start_date_after': date(2021, 8, 1).strftime('%Y-%m-%d'),
        'start_date_before': date(2021, 8, 31).strftime('%Y-%m-%d')
    }
    res = requests.get(url, params=payload)
    return res.json()['reservation_frame']

def is_time_slot_available(t):
    if t['is_published'] and t['reservation_cnt'] < t['reservation_cnt_limit']:
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
    ret += '空き: {}件 (最大: {}件)\n'.format((t['reservation_cnt_limit'] - t['reservation_cnt']), t['reservation_cnt_limit'])
    ret += '(2回目予定: {} {}-{})'.format(next_d, next_start_time, next_end_time)
    return ret

if __name__ == '__main__':
    time_slots = fetch_time_slots()
    available_time_slot = [t for t in time_slots if is_time_slot_available(t)]
    if len(available_time_slot) == 0:
        print('No time slot avaliable.')
        exit()
    message = 'ワクチン接種予約に空きがあるようですよ。\n{}'.format(LOGIN_URL)
    for t in available_time_slot:
        message += display_format_time_slot(t)
    create_line_message(message)
