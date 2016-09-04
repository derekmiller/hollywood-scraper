from lxml import etree
import psycopg2
from io import StringIO, BytesIO
import requests
import sys
from datetime import datetime

def get_dates():
    today = datetime.today()
    thisMonth = [today.month, today.year]
    def nextMonth(month):
        if month == 12:
            return [month + 1, today.year + 1]
        else:
            return [month + 1, today.year]
    return [thisMonth, nextMonth(today.month)]

def build_uri(month):
    base_uri = 'http://hollywoodtheatre.org/wp-admin/admin-ajax.php?action=aec_ajax&aec_type=widget&aec_widget_id=aec_widget-5-container'
    month_arg = '&aec_month=' + str(month[0])
    year_arg = '&aec_year=' + str(month[1])
    uri = base_uri + month_arg + year_arg
    return uri

def make_request(uri):
    page = requests.get(uri)
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(page.text), parser)
    days = tree.xpath('//div[@class=\'aec-event-info\']')
    return days

def parse_html(days):
    showings = []
    for day in days:
        date = day.xpath('h2[@class=\'widgettitle\']/text()')[0]
        date = date.replace("Showing ", "")
        date = datetime.strptime(date, '%B %d, %Y')
        films = day.xpath('.//li[@class=\'aec-tooltip-feed-agile\']')

        for film in films:
            film_details = film.xpath('.//p')
            film_title_times = film_details[0].xpath('strong/text()')[0]
            film_title_times = film_title_times.split(' |  ')
            url = film_details[1].xpath('a/@href')[0]
            title = film_title_times[0]
            times = film_title_times[1]
            times = times.split()

            for time in times:
                time = datetime.strptime(time, '%I:%M%p')
                time = date.replace(hour=time.hour, minute=time.minute)
                showings.append({'title': title, 'time': time, 'url': url})

    return showings

def save_to_db(showings):
    conn = psycopg2.connect("dbname=hollywood user=derekmiller")
    cur = conn.cursor()

    # CREATE TABLE showings (id serial PRIMARY KEY, title varchar, time timestamp, url varchar, UNIQUE (title, time));

    for showing in showings:
        try:
            cur.execute('INSERT INTO showings (title, time, url) VALUES (%s, %s, %s)',
                        (showing['title'], showing['time'], showing['url']))
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            continue
    cur.close()
    conn.close()

def main():
    months = get_dates()
    this_month_uri = build_uri(months[0])
    next_month_uri = build_uri(months[1])
    this_month_response = make_request(this_month_uri)
    next_month_response = make_request(next_month_uri)
    responses = this_month_response + next_month_response
    showings = parse_html(responses)
    save_to_db(showings)

main()
