from garden import Garden
from datetime import date, datetime, timedelta

garden = Garden()

today = datetime.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

oldest = yesterday.timestamp()
latest = tomorrow.timestamp()

garden.collect_slack_messages(oldest, latest)