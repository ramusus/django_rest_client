# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect, HttpResponse, Http404
from utils import JsonResponse
from models import Car, CarRest

def car(request):
    car = Car(model='Honda', color='blue')
    dict = car.__dict__
    del dict['_state'], dict['id']
    return HttpResponse(str(dict))