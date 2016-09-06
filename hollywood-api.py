from flask import Flask
from flask import jsonify
from flask import request
import psycopg2
import datetime

app = Flask(__name__)

@app.route('/')
def get_showings():
    conn = psycopg2.connect("dbname=hollywood user=derekmiller")
    cur = conn.cursor()

    start_date = request.headers.get('start_date')
    end_date = request.headers.get('end_date')

    if (start_date == None or start_date == '') and (end_date == None or end_date == ''):
        start_date = datetime.datetime.today()
        end_date = start_date + datetime.timedelta(days=7)
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
    elif end_date == None or end_date == '':
        end_date = start_date
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
        print(start_date, end_date)
    except ValueError:
        return jsonify({'errors': {'status': '400', 'details': 'Incorrect date format. Should be \'year-month-day\''}})

    cur.execute('SELECT * FROM showings WHERE time BETWEEN %s AND %s;', (start_date, end_date))
    data = cur.fetchall()
    showings = []
    for x in data:
        _id = x[0]
        title = x[1]
        time = x[2]
        url = x[3]
        showings.append({'id': _id, 'title': title, 'time': time, 'url': url})
    return jsonify(showings)

    cur.close()
    conn.close()
