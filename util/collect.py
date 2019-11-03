import requests
from datetime import date, datetime, timedelta

today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

start = yesterday.strftime('%Y-%m-%d')
end = tomorrow.strftime('%Y-%m-%d')
response = requests.get("http://localhost/attendance/collect/?start=%s&end=%s" % (start, end))
print(response.text)