# -*- coding: utf-8 -*-
import os
import re

from pkg_resources import resource_filename
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.util.translation import domain_functions
from trac.web.chrome import add_notice, add_warning, add_stylesheet, add_script_data, ITemplateProvider

gettext, _, tag_, N_, add_domain = domain_functions('ticket_template', 'gettext', '_', 'tag_', 'N_', 'add_domain')


class TicketTemplateAdmin(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        self.log.debug('access to ticket_template admin panel. %s', req)
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('ticket', _("Ticket System"), 'templates', _("Ticket Template"))

    def render_admin_panel(self, req, category, page, path_info):
        data = {
            'tid': req.args.get('tid', ''),
            'enabled': req.args.get('enabled', '0') == '1',
            'field_name': req.args.get('field_name', ''),
            'field_value': req.args.get('field_value', ''),
            'template': req.args.get('template', ''),
        }
        self.log.debug('request to ticket_template admin. '
                       'category: %s, page: %s, path_info: %s', category, page, path_info)
        if req.method == 'POST':
            tid = data['tid']
            field_name = data['field_name']
            field_value = data['field_value']
            template = data['template']
            enabled = data['enabled']
            if not tid:
                add_warning(req, _('ID is required.'))
            elif not re.match(r'^[\w\-]+$', tid):
                add_warning(req, _('ID contains invalid character(s).'))
            elif req.args.get('update') or req.args.get('save'):
                template_path = os.path.join(self.env.path, 'htdocs', 'ticket_templates', field_name)
                fd = open(template_path, 'w')
                fd.write(template)
                fd.close()
                self.config.set('ticket-template', tid, enabled and 'enabled' or 'disabled')
                self.config.set('ticket-template', tid + '.field_name', field_name)
                self.config.set('ticket-template', tid + '.field_value', field_value)
                self.config.set('ticket-template', tid + '.file', template_path)
                self.config.save()
                add_notice(req, _('Your changes have been saves.'))
            elif req.args.get('remove'):
                template_path = self.config.get('ticket-template', tid + '.file')
                if template_path and os.path.exists(template_path):
                    os.remove(template_path)
                for i, suffix in ('', '.field_name', '.field_value', '.file'):
                    self.config.remove('ticket-template', tid + suffix)
                self.config.save()
                for key in data.keys():
                    data[key] = ''
                add_notice(req, _('Your changes have been saves.'))

        data['base_url'] = self.env.base_url.rstrip('/')
        add_script_data(req, {
            'chrome_site_base_url': self.env.abs_href('/chrome/site'),
        })
        add_stylesheet(req, 'ticket_template/admin.css')
        return 'admin_ticket_template.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ticket_template', resource_filename(__name__, 'htdocs'))]
