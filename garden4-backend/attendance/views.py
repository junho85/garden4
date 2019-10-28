from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from .garden import Garden
import pprint


# Create your views here.
def index(request):
    context = {}
    return render(request, 'attendance/index.html', context)


def users(request):
    garden = Garden()
    users = garden.get_member()
    return JsonResponse(users, safe=False)


def user(request, user):
    garden = Garden()
    result = garden.find_attend_by_user(user)

    output = {}
    output[user] = []

    for (date, commits) in result.items():
        output[user].append({"date":date, "commits": commits})
        print(date)

    return JsonResponse(output)


def collect(request):
    oldest = datetime(2019, 10, 27).timestamp()
    latest = datetime(2019, 10, 29).timestamp()

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
    pprint.pprint(result)
    return JsonResponse(result, safe=False)