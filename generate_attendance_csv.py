from datetime import date, timedelta, datetime
from garden import Garden
import configparser

garden = Garden()

config = configparser.ConfigParser()
config.read('config.ini')

users = config['GITHUB']['USERS'].split(',')

attend_dict = {}

for user in users:
    attends = garden.find_attend_by_user(user)
    attend_dict[user] = attends


result = {}

selected_date = datetime(2019, 10, 24).date()
print("=======")
for days in range(10):
    # print dates
    print(selected_date, end=',')

    # make users - dates - first_ts
    for user in attend_dict:
        if user not in result:
            result[user] = {}

        result[user][selected_date] = ""

        if selected_date in attend_dict[user]:
            result[user][selected_date] = attend_dict[user][selected_date][0]["ts"]

    selected_date = selected_date + timedelta(days=1)

print("")
print("=======")

# print result csv
for (user, dates) in result.items():
    for (date, first_ts) in dates.items():
        print(first_ts, end=',')
    print("")

