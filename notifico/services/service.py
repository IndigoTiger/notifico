# -*- coding: utf8 -*-
__all__ = ('Service',)
import json

import redis

from notifico import app


class Service(object):
    COMMIT = 'commit'
    RAW = 'raw'
    ISSUE = 'issue'
    WIKI = 'wiki'

    COLORS = dict(
        RESET='\0x03',
        WHITE='\0x03' + '00',
        BLACK='\0x03' + '01',
        BLUE='\0x03' + '02',
        GREEN='\0x03' + '03',
        RED='\0x03' + '04',
        BROWN='\0x03' + '05',
        PURPLE='\0x03' + '06',
        ORANGE='\0x03' + '07',
        YELLOW='\0x03' + '08',
        LIGHT_GREEN='\0x03' + '09',
        TEAL='\0x03' + '10',
        LIGHT_CYAN='\0x03' + '11',
        LIGHT_BLUE='\0x03' + '12',
        PINK='\0x03' + '13'
    )

    @staticmethod
    def service_id():
        """
        A unique numeric identifier for this service.
        """
        raise NotImplementedError()

    @staticmethod
    def service_name():
        """
        A unique, human-readable name for this service.
        """
        raise NotImplementedError()

    @staticmethod
    def service_url():
        """
        The URL of the service provider, if one exists.
        """
        raise NotImplementedError()

    @staticmethod
    def service_description():
        """
        A description of this service.
        """
        raise NotImplementedError()

    @staticmethod
    def handle_request(user, request, hook):
        """
        Called on each HTTP request to extract and emit messages.
        """
        raise NotImplementedError()

    @classmethod
    def _request(cls, user, request, hook):
        """
        Called on each HTTP request.
        """
        r = redis.StrictRedis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB']
        )
        for message in cls.handle_request(user, request, hook):
            for channel in hook.project.channels:
                message['channel'] = dict(
                    host=channel.host,
                    port=channel.port,
                    ssl=channel.ssl,
                    channel=channel.channel
                )
                r.publish(
                    'message',
                    json.dumps(message)
                )
