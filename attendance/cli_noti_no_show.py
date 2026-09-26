from garden import Garden
from datetime import date, datetime, timedelta
import slack

garden = Garden()

garden.send_no_show_message()