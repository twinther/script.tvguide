import simplejson
import datetime
import time

json = simplejson.load(open('tv2.json'))

for program in json['result']:
	t = time.strptime(program['pg_start'], '%Y-%m-%dT%H:%M:%S.0000000+02:00')
	print str(datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)) + " - " + program['pro_title']
