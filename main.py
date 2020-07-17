import os
from flask import Flask
from flask.json import jsonify
from googleapiclient.discovery import build
import requests
import csv
from pytz import timezone

from datetime import date, datetime, tzinfo

app = Flask(__name__)

RH_DAY_1 = date(2020, 7, 10)

RH_SPREADSHEET_ID = '1wq_i99CWPCbmSjQGuqR7LROOnrCS8aBvbsbBgENMgH0'
TIME_ZONE = timezone('America/New_York')

PETE_MILEAGE = [
    80.90, # 9/12 1
    80.28, # 9/13 2
    73.55, # 9/14 3
    72.95, # 9/15 4
    73.63, # 9/16 5
    69.73, # 9/17 6
    0, # 9/18 7
    70.37, # 9/19 8
    70.63, # 9/20 9
    70.51, # 9/21 10
    72.35, # 9/22 11
    69.94, # 9/23 12
    71.05, # 9/24 13
    74.98, # 9/25 14
    71.47, # 9/26 15
    70.75, # 9/27 16
    70.18, # 9/28 17
    72.87, # 9/29 18
    72.31, # 9/30 19
    69.96, # 10/1 20
    73.78, # 10/2 21
    72.02, # 10/3 22
    77.66, # 10/4 23
    72.48, # 10/5 24
    74.25, # 10/6 25
    72.98, # 10/7 26
    71.24, # 10/8 27
    72.0, # 10/9 28
    72.01, # 10/10 29
    73.88, # 10/11 30
    72.25, # 10/12 31
    72.81, # 10/13 32
    72.36, # 10/14 33
    72, # 10/15 34
    73.3, # 10/16 35
    73.36, # 10/17 36
    71.89, # 10/18 37
    73.56, # 10/19 38
    71.98, # 10/20 39
    72.16, # 10/21 40
    73.7, # 10/22 41
    71.29, # 10/23 42
    88.28, # 10/24 43
]

@app.route('/api/rh_mileage')
def rh_mileage():
    service = build('sheets', 'v4', developerKey=os.environ['API_KEY'])
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=RH_SPREADSHEET_ID, range='Form Responses 1!G1').execute()
    values = result.get('values', [])

    rh_miles = float(values[0][0])
    miles_left = rh_miles
    day = 0
    while PETE_MILEAGE[day] <= miles_left:
        miles_left -= PETE_MILEAGE[day]
        day += 1

    with requests.Session() as s:
        download = s.get(f'http://rh-vs-pete.ue.r.appspot.com/route/day{day + 1}.csv')
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines()[1:])
        trkpts = list(cr)

    percent_done = miles_left / PETE_MILEAGE[day]
    trk_mileage = float(trkpts[-1][2])
    rh_mileage_pt = percent_done * trk_mileage
    rh_pos = (float(trkpts[0][0]), float(trkpts[0][1]))
    for trkpt in trkpts:
        if float(trkpt[2]) > rh_mileage_pt:
            break
        rh_pos = (float(trkpt[0]), float(trkpt[1]))

    return jsonify({'rh_dist': rh_miles, 'rh_pos': rh_pos})

@app.route('/api/pete_mileage')
def pete_mileage():
    event_day = (datetime.now(TIME_ZONE).date() - RH_DAY_1).days + 1
    now = datetime.now(TIME_ZONE)

    with requests.Session() as s:
        download = s.get(f'http://rh-vs-pete.ue.r.appspot.com/route/day{event_day}.csv')
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines()[1:])
        trkpts = list(cr)

    if now.hour < 6:
        pete_total_mileage = sum(PETE_MILEAGE[0:event_day-1])
        pete_pos = (float(trkpts[0][0]), float(trkpts[0][1]))
    elif now.hour > 18:
        pete_total_mileage = sum(PETE_MILEAGE[0:event_day])
        pete_pos = (float(trkpts[-1][0]), float(trkpts[-1][1]))
    else:
        minutes_since_6am = (now - now.replace(hour=6, minute=0, second=0, microsecond=0)).total_seconds() / 60
        percent_of_day = minutes_since_6am / (12 * 60)
        pete_total_mileage = sum(PETE_MILEAGE[0:event_day-1]) + (percent_of_day * PETE_MILEAGE[event_day - 1])

        trk_mileage = float(trkpts[-1][2])
        pete_mileage_pt = percent_of_day * trk_mileage
        pete_pos = (float(trkpts[0][0]), float(trkpts[0][1]))
        for trkpt in trkpts:
            if float(trkpt[2]) > pete_mileage_pt:
                break
            pete_pos = (float(trkpt[0]), float(trkpt[1]))

    return jsonify({'pete_mileage': round(pete_total_mileage, 2), 'pete_pos': pete_pos, 'event_day': event_day})

