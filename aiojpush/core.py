import asyncio
import logging

import aiohttp

from . import common
from .push import Push

logger = logging.getLogger('jpush')


class AioJPush:
    def __init__(self, key, secret, timeout=30, zone='default'):
        self.key = key
        self.secret = secret
        self.timeout = timeout
        self.zone = zone
        conn = aiohttp.TCPConnector(limit=1024)
        self._session = aiohttp.ClientSession(
            connector=conn,
            skip_auto_headers={'Content-Type'},
            auth=aiohttp.BasicAuth(key, secret),
        )

    def __del__(self):
        if not self._session.closed:
            if self._session._connector is not None \
                    and self._session._connector_owner:
                self._session._connector.close()
            self._session._connector = None

    async def _do_request(self, method, body, url,
                          content_type=None, version=None, params=None):
        headers = {
            'user-agent': 'jpush-api-python-client',
            'connection': 'keep-alive',
            'content-type': 'application/json;charset:utf-8',
        }

        logger.debug("Making %s request to %s. Headers:\n\t%s\nBody:\n\t%s",
                     method, url, '\n\t'.join(
                '%s: %s' % (key, value) for (key, value) in headers.items()),
                     body)
        try:
            async with self._session.request(method, url, data=body,
                                             params=params,
                                             headers=headers,
                                             timeout=self.timeout) as aio_resp:

                response = await common.CommonResponse.create(aio_resp)

        except asyncio.TimeoutError:
            raise common.APIConnectionException(
                "Connection to api.jpush.cn timed out.")
        except Exception as e:
            logger.exception('aiojpush error')
            raise common.APIConnectionException(
                "Connection to api.jpush.cn error.")

        if response.status_code == 401:
            raise common.Unauthorized(
                "Please check your AppKey and Master Secret")
        elif not (200 <= response.status_code < 300):
            raise common.JPushFailure.from_response(response)
        return response

    def set_logging(self, level):
        level_list = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
        if level in level_list:
            if level == "CRITICAL":
                logging.basicConfig(level=logging.CRITICAL)
            if level == "ERROR":
                logging.basicConfig(level=logging.ERROR)
            if level == "WARNING":
                logging.basicConfig(level=logging.WARNING)
            if level == "INFO":
                logging.basicConfig(level=logging.INFO)
            if level == "DEBUG":
                logging.basicConfig(level=logging.DEBUG)
            if level == "NOTSET":
                logging.basicConfig(level=logging.NOTSET)
        else:
            print("set logging level failed ,the level is invalid.")

    def create_push(self):
        """Create a Push notification."""
        return Push(self)
