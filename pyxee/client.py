# -*- coding: utf-8 -*-

"""Main module."""
import auth

CLIENT_ID = 'nLeOViYV6naLppNITK08'
CLIENT_SECRET = 'ETtCqgP41jT44g3LeiWL'

class XeeClient(object):
    def __init__(self, client_id, client_secret):
        self.api = auth.XeeAPI(client_id, client_secret)

    def auth(self):
        # Opinionated way to auth
        # TODO(sbauza): Do more intelligence
        if not self.api.authenticated:
            self.api.web_flow()
            self.api.grant()
