
#MLB API Methdos

from django.http import HttpResponse
import mlb_scores


def index(request):
    return HttpResponse("Welcome to the Scorepion API.")


