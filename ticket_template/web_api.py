# -*- coding: utf-8 -*-
import json
import os

from trac.cache import cached
from trac.core import Component, implements
from trac.ticket import TicketSystem
from trac.web import IRequestHandler


class TicketTemplateProvider(Component):

    implements(IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        return '/ticket-template/contexts.json' == req.path_info

    def process_request(self, req):
        req.send(json.dumps(self.contexts), 'application/json')

    # other methods

    def get_ticket_fields(self):
        return TicketSystem(self.env).get_ticket_fields()

    @cached
    def contexts(self, db=None):
        contexts = {}
        for key, value in self.config.options('ticket-template'):
            tid = key
            if '.' in key:
                tid = '.'.join(key.split('.')[0:-1])
            ctx = contexts.get(tid)
            if tid not in contexts:
                ctx = {'tid': tid}
                contexts[tid] = ctx
            if tid == key:
                name = 'enabled'
                value = self.config.getbool('ticket-template', key)
            else:
                name = key.split('.')[-1]
            ctx[name] = value
        return contexts.values()

    def get_ticket_template(self, tid):
        path = self.config.get('ticket-template', tid + '.file')
        if os.path.exists(path):
            with open(path) as fd:
                return fd.read()
        return None
