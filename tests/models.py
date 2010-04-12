# -*- coding: utf-8 -*-
from django.db import models
from rest_client import models as models_rest

class Car(models.Model):
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=100)

class CarRest(models_rest.Model):
    class Rest:
        url = '/api/car'
        fields = {
            'model': 'model',
            'car': 'car',
        }

    model = models.CharField(max_length=100)
    color = models.CharField(max_length=100)