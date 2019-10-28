from datetime import date, timedelta, datetime
from garden import Garden

oldest = datetime(2019, 10, 27).timestamp()
latest = datetime(2019, 10, 29).timestamp()

garden = Garden()
garden.collect_slack_messages(oldest, latest)
