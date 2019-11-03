import configparser
from datetime import date, timedelta, datetime
import slack
import pymongo
import pprint
import os


class Garden:
    def __init__(self):
        config = configparser.ConfigParser()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'config.ini')
        config.read(path)

        slack_api_token = config['DEFAULT']['SLACK_API_TOKEN']
        self.slack_client = slack.WebClient(token=slack_api_token)

        self.channel_id = config['DEFAULT']['CHANNEL_ID']

        self.mongo_database = config['MONGO']['DATABASE']
        self.mongo_host = config['MONGO']['HOST']
        self.mongo_port = config['MONGO']['PORT']

        # mongodb collections
        self.mongo_collection_slack_message = "slack_messages"

        # users list ['junho85', 'user2', 'user3']
        self.users = config['GITHUB']['USERS'].split(',')

        self.start_date = datetime(2019, 10, 1).date() # 2019-10-01

    def connect_mongo(self):
        return pymongo.MongoClient("mongodb://%s:%s" % (self.mongo_host, self.mongo_port))

    def get_member(self):
        return self.users

    def find_attend(self, oldest, latest):
        print("find_attend")
        print(oldest)
        print(datetime.fromtimestamp(oldest))
        print(latest)
        print(datetime.fromtimestamp(latest))

        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        for message in mongo_collection.find({"ts_for_db": {"$gte": datetime.fromtimestamp(oldest), "$lt": datetime.fromtimestamp(latest)}}):
            print(message["ts"])
            print(message)

    # 특정 유저의 전체 출석부를 생성함
    # TODO 출석부를 DB에 넣고 마지막 생성된 출석부 이후의 데이터로 추가 출석부 만들도록 하자
    def find_attendance_by_user(self, user):
        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        result = {}

        start_date = self.start_date
        for message in mongo_collection.find({"attachments.author_name": user}).sort("ts", 1):
            # make attend
            commits = []
            for attachment in message["attachments"]:
                commits.append(attachment["text"])
            # ts_datetime = datetime.fromtimestamp(float(message["ts"]))
            ts_datetime = message["ts_for_db"]
            attend = {"ts": ts_datetime, "message": commits}

            # current date and date before day1
            date = ts_datetime.date()
            date_before_day1 = date - timedelta(days=1)
            hour = ts_datetime.hour

            if date_before_day1 >= start_date and hour < 4 and date_before_day1 not in result:
                # check before day1. if exists, before day1 is already done.
                result[date_before_day1] = []
                result[date_before_day1].append(attend)
            else:
                # create date commits array
                if date not in result:
                    result[date] = []

                result[date].append(attend)

        return result

    # github 봇으로 모은 slack message 들을 slack_messages collection 에 저장
    def collect_slack_messages(self, oldest, latest):
        # print(oldest)
        # print(datetime.fromtimestamp(oldest))
        # print(latest)
        # print(datetime.fromtimestamp(latest))
        # print(self.channel_id)

        response = self.slack_client.channels_history(
            channel=self.channel_id,
            latest=str(latest),
            oldest=str(oldest),
            count=10000
        )

        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        for message in response["messages"]:
            message["ts_for_db"] = datetime.fromtimestamp(float(message["ts"]))
            # pprint.pprint(message)

            try:
                mongo_collection.insert_one(message)
            except pymongo.errors.DuplicateKeyError as err:
                print(err)
                continue

    def remove_all_slack_messages(self):
        conn = self.connect_mongo()

        mongo_database = self.mongo_database

        db = conn.get_database(mongo_database)

        mongo_collection = db.get_collection(self.mongo_collection_slack_message)
        mongo_collection.remove()

    """
    특정일의 출석 데이터 불러오기
    @param selected_date
    """
    def get_attendance(self, selected_date):
        attend_dict = {}

        # get all users attendance info
        for user in self.users:
            attends = self.find_attendance_by_user(user)
            attend_dict[user] = attends

        result = {}
        result_attendance = []

        # make users - dates - first_ts
        for user in attend_dict:
            if user not in result:
                result[user] = {}

            result[user][selected_date] = None

            if selected_date in attend_dict[user]:
                result[user][selected_date] = attend_dict[user][selected_date][0]["ts_for_db"]

            result_attendance.append({"user": user, "first_ts": result[user][selected_date]})

        return result_attendance

    def generate_attendance_csv(self):
        attend_dict = {}

        for user in self.users:
            attends = self.find_attendance_by_user(user)
            attend_dict[user] = attends

        result = {}

        selected_date = datetime(2019, 10, 24).date()
        # selected_date = datetime.strptime("20191024", "%Y%m%d").date()
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
                # print(date, first_ts)
                print(first_ts, end=',')
            print("")