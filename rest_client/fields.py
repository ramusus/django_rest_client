# -*- coding: utf-8 -*-
from django.db import models
from django.core import exceptions

class Field(models.Field):

    rest_name = None
    backend_generated = False
    value = None

    def __init__(self, rest_name=None, backend_generated=False, **kwargs):
        self.rest_name = rest_name
        self.backend_generated = backend_generated

        super(Field, self).__init__(**kwargs)
        if self.has_default():
            self.set_value(self.default)

    def set_value(self, value):
        self.value = self.to_python(value)

    def __repr__(self):
        return str(self.value) or '<%s: None>' % self.get_internal_type()

class DateTimeField(Field, models.DateTimeField):

    def to_python(self, value):
        '''
        Try to parse by django built-in DateTimeField mechanism, and if fails by dateutil.parser library
        '''
        try:
            return super(DateTimeField, self).to_python(value)
        except exceptions.ValidationError:
            try:
                from dateutil.parser import parse
            except ImportError:
                raise ValueError("Can not parse '%s' value to datetime instance" % value)
            return parse(value)

class ArrayField(Field, list):

    type = None

    def __init__(self, items_type, **kwargs):
        from models import Model
        if items_type in (str,int,unicode) or issubclass(items_type, Model):
            self.type = items_type
        else:
            raise TypeError("Error type attribute, it must be str, unicode, int or subclass of Model, but got %s" % items_type)

        super(ArrayField, self).__init__(**kwargs)

    def __getitem__(self, i):
        if i >= len(self.value):
            raise IndexError("list index out of range")
        else:
            return self.value[i]

    def get_internal_type(self):
        return "ArrayField"

    def to_python(self, value):
        if value is not None:
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, self.type):
                        continue
                    value[i] = self.type(item)
            else:
                raise TypeError("Error type of ArrayField, list expected, got %s" % type(value))
        return value

class BooleanField(Field, models.BooleanField):
    pass

class IntegerField(Field, models.IntegerField):
    pass

class CharField(Field, models.CharField):
    pass