# -*- coding: utf-8 -*-

"""Auth module."""
import logging
import webbrowser
logging.basicConfig(level=logging.DEBUG)


from gevent import monkey; monkey.patch_all()
import gevent
import gevent.pywsgi
from oauthlib.oauth2.rfc6749 import errors as oauth2_errors
import requests_oauthlib
from six.moves.urllib import parse as urlparse


XEE_ENDPOINT = 'https://cloud.xee.com/v3'


class XeeAPI(object):
    """Fairly generic Oauth2 authentication helper for Web application
       flows with authorization code grant.
    """
    def __init__(self, client_id, client_secret,
                 access_token=None, refresh_token=None):
        """Constructs a new OAuth2 client.

        :param client_id: the OAuth2 client ID for the Xee API
        :param client_secret: the OAuth2 client secret for the Xee API
        :param access_token: an OAuth2 access token, if existing.
                             UNSUPPORTED YET.
        :param refresh_token: an OAuth2 refresh token, if existing.
                              UNSUPORTED YET.
        """

        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = access_token
        self.refresh_token = refresh_token

        # OAuth2 session
        self.session = None

        self._server = None
        self._code = None


    @property
    def authenticated(self):
        return bool(self.access_token)

    # NOTE(sbauza): Only for the case when running the local WSGI server
    def _auth_wsgi_app(self, env, start_response):
        if env['PATH_INFO'] == '/':
            qs = env['QUERY_STRING']
            hascode = urlparse.parse_qs(qs).get('code')
            if hascode:
                # parse_qs returns a list of values for the same query variable
                try:
                    self._code = hascode[0]
                except IndexError:
                    pass
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [b"<b>Auth worked, you can close the window.</b>"]

        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return [b'<h1>Not Found</h1>']

    def web_flow(self, redirect_uri=None, run_server=True, server_port=8080):
        """Runs the web application flow which redirects to the provided URI.

           As the Xee API v3 only supports OAuth2 web application flows, we
           need to call the Xee landing page for asking user credentials.
           The redirect URI will be the one passed to the Xee API call, and if
           not provided, will default to either what the WSGI server provides
           or a fake URL.

           :param redirect_uri: The redirect URI to provide to the Xee
                                user authentication page.
        :param run_server: Flag to indicate whether to start a WSGI server
                           for the callback URL. If not started, you need to
                           pass the authorization response directly.
        :param server_port: The WSGI server port number, only if you choose it.
        """

        if self.access_token:
            # Nothing to do.
            return
        if run_server is True:
            self._server = gevent.pywsgi.WSGIServer(("127.0.0.1", server_port),
                                                   self._auth_wsgi_app)
            # This is a greenlet-based server, think asynchronously.
            # This is a NON-blocking call.
            self._server.start()

        if redirect_uri is None:
            if self._server:
                redirect_uri = "http://localhost:%s" % self._server.server_port
            else:
                # Arbitrary URL
                redirect_uri = "https://localhost/prettysureitsnoworking"
        self.session = requests_oauthlib.OAuth2Session(
            client_id=self.client_id, redirect_uri=redirect_uri)
        authorization_url, state = self.session.authorization_url(
            XEE_ENDPOINT + '/auth/auth')
        webbrowser.open(authorization_url)
        if self._server:
            while True:
                if self._code:
                    self._server.stop()
                    break
                gevent.sleep(0)

    def grant(self, code=None, authorization_response=None):
        """Calls the Xee API for getting tokens.

           Either accepting to pass a authorization code or directly the
           returned redirect URI.
           In case you don't pass either of them, it can use the code passed
           back to the WSGI server if you chose to run it.

           :param code: The authorization code returned by the Xee API.
           :param authorization_response: The redirect response returned by
                                          the Xee API.
        """
        if self.access_token:
            # Easy peasy.
            return self.access_token

        code = code or self._code
        if code:
            kwargs = {'code': code}
        elif authorization_response:
            kwargs = {'authorization_response': authorization_response}
        else:
            raise Exception('Please authenticate first.')
        try:
            token = self.session.fetch_token(
                XEE_ENDPOINT + '/auth/access_token',
                client_id=self.client_id, client_secret=self.client_secret,
                **kwargs)
        except oauth2_errors.MissingTokenError:
            raise Exception('Invalid OAuth2 credentials or code is invalid.')
        self.access_token = token['access_token']
        self.refresh_token = token['refresh_token']

    def get(self, url, *args, **kwargs):
        if not self.authenticated:
            raise Exception('Please authenticate first.')
        return self.session.get(XEE_ENDPOINT + url, *args, **kwargs)
