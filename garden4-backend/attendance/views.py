from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from .garden import Garden


# Create your views here.
def index(request):
    context = {}
    return render(request, 'attendance/index.html', context)


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