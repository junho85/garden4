import configparser
from datetime import date, timedelta, datetime
from slack_sdk import WebClient
import psycopg2
import psycopg2.extras
import json
import pprint
import os
import yaml
import pytz

class Garden:
    def __init__(self):
        config = configparser.ConfigParser()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'config.ini')
        config.read(path)

        slack_api_token = config['DEFAULT']['SLACK_API_TOKEN']
        self.slack_client = WebClient(token=slack_api_token)

        self.channel_id = config['DEFAULT']['CHANNEL_ID']

        # PostgreSQL settings
        self.pg_database = config['POSTGRESQL']['DATABASE']
        self.pg_host = config['POSTGRESQL']['HOST']
        self.pg_port = config['POSTGRESQL']['PORT']
        self.pg_user = config['POSTGRESQL']['USER']
        self.pg_password = config['POSTGRESQL']['PASSWORD']
        self.pg_schema = config['POSTGRESQL']['SCHEMA']

        self.gardening_days = config['DEFAULT']['GARDENING_DAYS']

        # users list ['junho85', 'user2', 'user3']
        self.users = config['GITHUB']['USERS'].split(',')

        # users_with_slackname
        path = os.path.join(BASE_DIR, 'users.yaml')

        with open(path) as file:
            self.users_with_slackname = yaml.safe_load(file)

        self.start_date = datetime.strptime(config['DEFAULT']['START_DATE'], "%Y-%m-%d").date()  # start_date e.g.) 2019-10-01
        
        # 타임존 설정
        self.kst = pytz.timezone('Asia/Seoul')

    def connect_postgres(self):
        conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
            user=self.pg_user,
            password=self.pg_password,
            sslmode='require'
        )
        # 연결 후 스키마 설정
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {self.pg_schema}")
        cursor.close()
        return conn

    def get_member(self):
        return self.users

    def get_gardening_days(self):
        return self.gardening_days

    '''
    github userid - slack username
    '''
    def get_members(self):
        return self.users_with_slackname

    def find_attend(self, oldest, latest):
        print("find_attend")
        print(oldest)
        print(datetime.fromtimestamp(oldest))
        print(latest)
        print(datetime.fromtimestamp(latest))

        conn = self.connect_postgres()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT ts, ts_for_db
            FROM slack_messages 
            WHERE ts_for_db >= %s AND ts_for_db < %s
        """
        
        cursor.execute(query, (datetime.fromtimestamp(oldest), datetime.fromtimestamp(latest)))
        messages = cursor.fetchall()

        for message in messages:
            print(message["ts"])
            print(message)

        cursor.close()
        conn.close()

    # 특정 유저의 전체 출석부를 생성함
    # TODO 출석부를 DB에 넣고 마지막 생성된 출석부 이후의 데이터로 추가 출석부 만들도록 하자
    def find_attendance_by_user(self, user):
        conn = self.connect_postgres()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # PostgreSQL 쿼리: JSONB 배열에서 author_name이 일치하는 메시지 찾기
        query = """
            SELECT ts, ts_for_db, attachments
            FROM slack_messages 
            WHERE attachments @> %s
            ORDER BY ts
        """
        
        # JSONB 쿼리 파라미터
        param = json.dumps([{"author_name": user}])
        
        cursor.execute(query, (param,))
        messages = cursor.fetchall()

        result = {}
        start_date = self.start_date
        
        for message in messages:
            # make attend
            commits = []
            attachments = message['attachments']
            if attachments:
                for attachment in attachments:
                    if attachment.get('author_name') == user:
                        commits.append(attachment.get('text', ''))
            
            # DB의 ts_for_db는 KST 시간이 UTC로 저장되어 있으므로 9시간을 빼서 올바른 KST로 변환
            ts_datetime_raw = message['ts_for_db']
            ts_datetime = ts_datetime_raw - timedelta(hours=9)
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

        cursor.close()
        conn.close()
        return result

    # github 봇으로 모은 slack message 들을 slack_messages 테이블에 저장
    def collect_slack_messages(self, oldest, latest):
        response = self.slack_client.conversations_history(
            channel=self.channel_id,
            latest=str(latest),
            oldest=str(oldest),
            limit=1000
        )

        conn = self.connect_postgres()
        cursor = conn.cursor()

        for message in response["messages"]:
            ts_for_db = datetime.fromtimestamp(float(message["ts"]))
            
            # PostgreSQL INSERT 쿼리
            insert_query = """
                INSERT INTO slack_messages (
                    ts, ts_for_db, bot_id, type, text, "user", team, 
                    bot_profile, attachments
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (ts) DO NOTHING
            """
            
            try:
                cursor.execute(insert_query, (
                    message.get("ts"),
                    ts_for_db,
                    message.get("bot_id"),
                    message.get("type"),
                    message.get("text"),
                    message.get("user"),
                    message.get("team"),
                    json.dumps(message.get("bot_profile")) if message.get("bot_profile") else None,
                    json.dumps(message.get("attachments")) if message.get("attachments") else None
                ))
            except Exception as err:
                print(f"Error inserting message: {err}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

    def remove_all_slack_messages(self):
        conn = self.connect_postgres()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM slack_messages")
        conn.commit()
        
        cursor.close()
        conn.close()

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
                result[user][selected_date] = attend_dict[user][selected_date][0]["ts"]

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

    def send_no_show_message(self):
        members = self.get_members()
        today = datetime.today().date()

        message = "미출석자 알람 테스트 "
        results = self.get_attendance(today)
        for result in results:
            if result["first_ts"] is None:
                message += "@%s " % members[result["user"]]["slack"]

        self.slack_client.chat_postMessage(
            channel='#junekim', # temp
            text=message,
            link_names=1
        )

    def test_slack(self):
        # self.slack_client.chat_postMessage(
        #     channel='#junekim', # temp
        #     text='@junho85 test',
        #     link_names=1
        # )
        response = self.slack_client.users_list()
        print(response)
