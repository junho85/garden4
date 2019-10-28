# garden4
* 정원사들 시즌4 출석부입니다.
* slack #commit 채널에 올라온 메시지들을 수집해서 출석부를 작성합니다.

## config.ini
* path: garden4-backend/attendance/config.ini
```
; config.ini
[DEFAULT]
SLACK_API_TOKEN = xoxp-...
CHANNEL_ID = CNP...

[MONGO]
DATABASE = garden
HOST = localhost
PORT = 27017

[GITHUB]
USERS = junho85,user2,user3
```

## WEB
* http://localhost:8000/attendance/

## API
* /attendance/user/<user> - user 의 출석 데이터를 불러옵니다.
  * e.g. /attendance/user/junho85 - junho85 의 출석 데이터를 불러옵니다.
* /attendance/collect/ - slack_messages 를 가져와서 db 에 넣습니다.
  * 구 collect_slack_messages.py
  * TODO 날짜 파라미터 받을 수 있도록
* /attendance/csv/ - 출석부 csv 만들기
  * 구 generate_attendance_csv.py
  * slack_messages 의 데이터를 읽어서 출석부를 csv 를 생성합니다.
  * 이 값을 스프레드시트에 붙여 넣어서 사용합니다.
  * TODO API 결과로 가져올 수 있도록
* /attendance/get/<date> - 특정 날짜의 출석부 조회하기
  * http://localhost:8000/attendance/get/20191028

## python modules
```
pip install pymongo
```

## mongodb
* create database
```
use garden
```

### slack_messages
* save all slack messages from #commit channel
```
{ts, attachments, bot_id, bot_profile, team, text, ts, type, user}
```

slack_messages 에 저장된 데이터 예. mongodb 에 넣으면서 _id 가 자동 추가 되고 ts 는 timestamp type 으로 변경해서 넣고 있음.
```
{
	'_id': ObjectId('5db5a705f7cf4f12ad0d8c1b'),
	'bot_id': 'BNGD110UR',
	'type': 'message',
	'text': '',
	'user': 'UNR1ZN80N',
	'ts': datetime.datetime(2019, 10, 2, 20, 57, 55, 26000),
	'team': 'TNMAF3TT2',
	'bot_profile': {
		'id': 'BNGD110UR',
		'deleted': False,
		'name': 'GitHub',
		'updated': 1569307567,
		'app_id': 'A8GBNUWU8',
		'icons': {
			'image_36': 'https://slack-files2.s3-us-west-2.amazonaws.com/avatars/2017-12-19/288981919427_f45f04edd92902a96859_36.png',
			'image_48': 'https://slack-files2.s3-us-west-2.amazonaws.com/avatars/2017-12-19/288981919427_f45f04edd92902a96859_48.png',
			'image_72': 'https://slack-files2.s3-us-west-2.amazonaws.com/avatars/2017-12-19/288981919427_f45f04edd92902a96859_72.png'
		},
		'team_id': 'TNMAF3TT2'
	},
	'attachments': [{
		'author_name': 'junho85',
		'fallback': '[junho85/TIL] <https://github.com/junho85/TIL/compare/33da42459485...a29a33f31b08|2 new commits> pushed to <https://github.com/junho85/TIL/tree/master|`master`>',
		'text': '*<https://github.com/junho85/TIL/compare/33da42459485...a29a33f31b08|2 new commits> pushed to <https://github.com/junho85/TIL/tree/master|`master`>*\n<https://github.com/junho85/TIL/commit/027dfe626170f09e8c1deb5e75b4fc4e9565ffce|`027dfe62`> - javascript - date - moment\n<https://github.com/junho85/TIL/commit/a29a33f31b08767a228701a4737c131d75902ab9|`a29a33f3`> - postgresql',
		'footer': '<https://github.com/junho85/TIL|junho85/TIL>',
		'id': 1,
		'author_link': 'https://github.com/junho85',
		'author_icon': 'https://avatars3.githubusercontent.com/u/1219373?v=4',
		'footer_icon': 'https://github.githubassets.com/favicon.ico',
		'color': '24292f',
		'mrkdwn_in': ['text']
	}]
}
```

* create collection
```
db.createCollection("slack_messages")
```
* create index. ts unique
```
db.slack_messages.createIndex({ts:1}, {unique: true})
```

### commits
* 유저별 커밋 내역들
* user
  * commits

### attendance
* 출석부
* dates
  * users
    * commits
* slack 메시지 올라오지 않은 케이스를 위해 수작업으로 넣어 준다면 type 이 필요할듯.

