from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
from .garden import Garden
import pprint
import markdown
import re


def process_slack_links(text):
    """
    Slack 링크 포맷 <url|text>를 HTML 링크로 변환
    """
    # <url|text> 패턴을 찾아서 <a href="url">text</a>로 변환
    pattern = r'<([^|>]+)\|([^>]+)>'
    def replace_link(match):
        url = match.group(1)
        text = match.group(2)
        # 백틱으로 둘러싸인 텍스트는 <code> 태그로 변환
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return f'<a href="{url}">{text}</a>'
    
    return re.sub(pattern, replace_link, text)


def index(request):
    garden = Garden()
    context = {
        "gardening_days": garden.get_gardening_days()
    }
    return render(request, 'attendance/index.html', context)


# 정원사들 리스트
def users(request):
    garden = Garden()
    users = garden.get_member()
    return JsonResponse(users, safe=False)


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


# 유저별 출석부
def user(request, user):
    garden = Garden()
    context = {
        "user": user,
        "gardening_days": garden.get_gardening_days()
    }

    return render(request, 'attendance/users.html', context)


# 유저의 출석데이터
def user_api(request, user):
    garden = Garden()
    result = garden.find_attendance_by_user(user)

    output = []
    for (date, commits) in result.items():
        for commit in commits:
            # Slack 링크 포맷을 먼저 처리한 후 마크다운 적용
            processed_text = process_slack_links(commit["message"][0])
            commit["message"][0] = markdown.markdown(processed_text)
            # commit["message"][0] = "<br>".join(commit["message"][0].split("\n"))
        output.append({"date": date, "commits": commits})

    return JsonResponse(output, safe=False)


# slack_messages 수집
def collect(request):
    oldest = datetime.strptime(request.GET.get('start'), "%Y-%m-%d").timestamp()
    latest = datetime.strptime(request.GET.get('end'), "%Y-%m-%d").timestamp()

    garden = Garden()
    garden.collect_slack_messages(oldest, latest)

    return JsonResponse({})


def csv(request):
    garden = Garden()
    garden.generate_attendance_csv()

    return JsonResponse({})


# 특정일의 출석 데이터 불러오기
def get(request, date):
    garden = Garden()
    result = garden.get_attendance(datetime.strptime(date, "%Y%m%d").date())
    # pprint.pprint(result)
    return JsonResponse(result, safe=False)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


# 전체 출석부 조회
def gets(request):
    garden = Garden()

    result = []

    users = garden.get_member()
    for user in users:
        attendances = garden.find_attendance_by_user(user)

        # convert key type datetime.date to string
        for key_date in list(attendances.keys()).copy():
            formatted_date = key_date.strftime("%Y-%m-%d")
            attendances[formatted_date] = attendances.pop(key_date)[0]["ts"]

        result.append({"user": user, "attendances": attendances})

    return JsonResponse(result, safe=False)