import configparser
from datetime import date, timedelta, datetime
import slack
import pymongo
import json
import pprint


class Garden:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        slack_api_token = config['DEFAULT']['SLACK_API_TOKEN']
        self.slack_client = slack.WebClient(token=slack_api_token)

        self.channel_id = config['DEFAULT']['CHANNEL_ID']

        self.mongo_database = config['MONGO']['DATABASE']
        self.mongo_host = config['MONGO']['HOST']
        self.mongo_port = config['MONGO']['PORT']

        # mongodb collections
        self.mongo_collection_slack_message = "slack_messages"

    def connect_mongo(self):
        return pymongo.MongoClient("mongodb://%s:%s" % (self.mongo_host, self.mongo_port))

    def find_attend(self, oldest, latest):
        print("find_attend")
        print(oldest)
        print(datetime.fromtimestamp(oldest))
        print(latest)
        print(datetime.fromtimestamp(latest))

        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        for message in mongo_collection.find({"ts": {"$gte": datetime.fromtimestamp(oldest), "$lt": datetime.fromtimestamp(latest)}}):
            print(message["ts"])
            print(message)

    def find_attend_by_user(self, user):
        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        result = {}

        start_date = datetime(2019, 10, 1).date()
        for message in mongo_collection.find({"attachments.author_name": user}).sort("ts", 1):
            # make attend
            commits = []
            for attachment in message["attachments"]:
                commits.append(attachment["text"])
            attend = {"ts": message["ts"], "message": commits}

            # current date and date before day1
            date = message["ts"].date()
            date_before_day1 = date - timedelta(days=1)
            hour = message["ts"].hour

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
        print(oldest)
        print(datetime.fromtimestamp(oldest))
        print(latest)
        print(datetime.fromtimestamp(latest))
        print(self.channel_id)

        response = self.slack_client.channels_history(
            channel=self.channel_id,
            latest=str(latest),
            oldest=str(oldest),
            count=1000
        )

        conn = self.connect_mongo()

        db = conn.get_database(self.mongo_database)
        mongo_collection = db.get_collection(self.mongo_collection_slack_message)

        for message in response["messages"]:
            message["ts"] = datetime.fromtimestamp(float(message["ts"]))
            pprint.pprint(message)

            try:
                mongo_collection.insert_one(message)
            except pymongo.errors.DuplicateKeyError:
                continue

    def remove_all_slack_messages(self):
        conn = self.connect_mongo()

        mongo_database = self.mongo_database

        db = conn.get_database(mongo_database)

        mongo_collection = db.get_collection(self.mongo_collection_slack_message)
        mongo_collection.remove()
