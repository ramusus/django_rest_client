# -*- coding: utf-8 -*-
from django.db import models
from django.core import exceptions
from django.conf import settings
from fields import CharField, DateTimeField, BooleanField, IntegerField, ArrayField
from urlparse import urljoin
import httplib
import urllib
import simplejson as json
import logging

__all__ = ['FailResponse', 'Manager', 'Model', 'CharField', 'DateTimeField', 'BooleanField', 'IntegerField', 'ArrayField']

class FailResponse(Exception):
    '''
    Exception raised if backend returns bad and fail response
    code - number for specified in API fail resposes
    '''
    code = None
    message = None

    def __init__(self, message, code=None):
        self.code = code
        self.message = message

    def __str__(self):
        return self.message

class Manager(object):

    model = None

    def all(self):
        '''
        Send GET request for all objects of model
        '''
        model_instance = self.model()
        raw_data = model_instance._request('GET', model_instance._get_object_url())
        objects = model_instance.get_response(raw_data)

        if not isinstance(objects, list):
            raise FailResponse("Response object must be list, not '%s'" % typ(objects))

        for i, object in enumerate(objects):
            model_instance = self.model()
            model_instance._parse_object(object)
            objects[i] = model_instance

        return objects

    def get(self, id=None, **kwargs):
        '''
        Send GET request and construct new instance from respose's fields
        '''
        model_instance = self.model(**kwargs)
        model_instance.get(id)
        return model_instance

    def create(self, **kwargs):
        '''
        Send POST request
        '''
        model_instance = self.model(**kwargs)
        model_instance.create()
        return model_instance

class Model(object):
    '''
    Base model for rest-clients models
    '''
    class Rest:
        pass

    objects = Manager()

    def __init__(self, object_dict=None, raw_data=None, **kwargs):

        setattr(self.objects, 'model', self.__class__)
        self._substitute_fields_and_generate_map()

        # set initial values
        for field_name, field in self.Rest.fields.items():
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            elif field.default != models.fields.NOT_PROVIDED:
                setattr(self, field_name, field.default)
            else:
                setattr(self, field_name, None)

        if raw_data:
            self.get_response(raw_data)
        elif object_dict:
            self._parse_object(object_dict)

    def __setattr__(self, name, value, field=None):
        '''
        Set value to local attribute and atrubute of field in self.Rest.fields dictionary
        '''
        if not field and hasattr(self.Rest, 'fields') and name in self.Rest.fields:
            field = self.Rest.fields[name]
            try:
                field.set_value(value)
                super(Model, self).__setattr__(name, field.value)
            except:
                raise ValueError("Can not set value '%s' to field '%s' with type '%s'" % (value, name, type(field)))
        else:
            super(Model, self).__setattr__(name, value)

    def _get_object_url(self, id=None):
        if id:
            url = self.Rest.url + '/' if self.Rest.url[-1] != '/' else self.Rest.url
            return urljoin(url, str(id))
        else:
            return self.Rest.url

    def get(self, id):
        self._request_parse('GET', id=id)

    def create(self):
        params = self.get_rest_params()
        self._request_parse('POST', params=params)

    def _request_parse(self, method, id=None, params=None):
        raw_data = self._request(method, self._get_object_url(id), params)
        object = self.get_response(raw_data)
        self._parse_object(object)

    def delete(self):
        self._request('DELETE', self._get_object_url(self.id))
        self.id = None
        return True

    def save(self):
        return self._request('PUT', self._get_object_url(self.id))

    def _request(self, type, url, params=None):

        if not params:
            params = {}
        from django.utils.importlib import import_module

        # update dict params by common parameters
        if hasattr(settings, 'REST_CLIENT_COMMON_PARAMETERS'):
            mod_name = '.'.join(settings.REST_CLIENT_COMMON_PARAMETERS.split('.')[:-1])
            func_name = settings.REST_CLIENT_COMMON_PARAMETERS.split('.')[-1]
            func = getattr(import_module(mod_name), func_name)
            if not callable(func):
                raise ValueError("Value of settings.REST_CLIENT_COMMON_PARAMETERS must be callable function with one argument")
            params = func(params)

        params = urllib.urlencode(params)

        if type in ['GET','DELETE']:
            url += '?'+params
            body = ''
        else:
            body = params

        if hasattr(self.Rest, 'domain'):
            domain = self.Rest.domain
        elif hasattr(settings, 'REST_CLIENT_DOMAIN'):
            domain = settings.REST_CLIENT_DOMAIN
        else:
            raise ValueError("You must specified domain in settings.REST_CLIENT_DOMAIN or Rest.domain attribute")

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'User-Agent': settings.REST_CLIENT_USERAGENT if hasattr(settings, 'REST_CLIENT_USERAGENT') else 'django_rest_client/0.1',
        }

        conn = httplib.HTTPConnection(domain)
        conn.request(type, url, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        if hasattr(settings, 'REST_CLIENT_LOG'):
            logging.basicConfig(filename=settings.REST_CLIENT_LOG, level=logging.DEBUG, format='\n[%(asctime)s] %(message)s')
            logging.info('%(type)s %(url)s HTTP/1.1\n%(headers)s\n\n%(body)s' % {
                'body': body,
                'type': type,
                'url': url,
                'headers': '\n'.join([': '.join([key, value]) for key, value in headers.items() + [('Host',domain)]])
            })
            logging.info(data)

        return data

    def get_response(self, raw_data):
        '''
        Parse response, check status of response and return object in 'data' field
        '''
        try:
            data = json.loads(raw_data)
        except:
            raise FailResponse("Can not parse response with content '%s'" % raw_data)

        if data['response'] == 'ok':
            if 'data' in data:
                return data['data']
            else:
                return data
        elif data['response'] == 'fail':
            raise FailResponse("Request failed with error %d (%s)" % (data['code'], data['message']), data['code'])
        else:
            raise FailResponse("Can not find response key in content '%s'" % raw_data)

    def _substitute_fields_and_generate_map(self):
        '''
        Generate dict of fields self.Rest.fields and substitute values to attributes
        generate dict of mapping local attribute names to fieldnames self.Rest.fields_map for using in API
        '''
        fields = {}
        fields_map = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, models.Field):
                fields_map[attr_name] = attr.rest_name or attr_name
                fields[attr_name] = attr
                setattr(self, attr_name, attr.value)

        self.Rest.fields = fields
        self.Rest.fields_map = fields_map

    def _parse_object(self, object):
        '''
        Go through attributes mapping dict and set values from REST response to every attribute
        '''
        for attr_name, rest_name in self.Rest.fields_map.items():
            if rest_name in object:
                value = object[rest_name]
                attr = self.Rest.fields[attr_name]
                setattr(self, attr_name, value)

    def get_rest_params(self):
        '''
        Generate parameters for request
        '''
        params = {}
        for field_name, field in self.Rest.fields.items():
            if not field.backend_generated:
                params[self.Rest.fields_map[field_name]] = getattr(self, field_name)
        return params
