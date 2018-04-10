# -*- coding: utf-8 -*-
import os
import re

from pkg_resources import resource_filename
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.ticket import TicketSystem
from trac.util import translation
from trac.web.chrome import add_notice, add_warning, add_stylesheet, add_script_data, ITemplateProvider, Chrome

_, tag_, N_, add_domain = translation.domain_functions('ticket_template', '_', 'tag_', 'N_', 'add_domain')


class TicketTemplateAdmin(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        self.log.debug('access to ticket_template admin panel. %s', req)
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('ticket', _("Ticket System"), 'templates', _("Ticket Templates"))

    def render_admin_panel(self, req, category, page, path_info):
        data = {
            'id': req.args.get('id', ''),
            'name': req.args.get('name', ''),
            'description': req.args.get('description', ''),
            'enabled': req.args.get('enabled', '0') == '1',
            'field_name': req.args.get('field_name', ''),
            'field_value': req.args.get('field_value', ''),
            'template': req.args.get('template', ''),
            'fields': self.get_ticket_fields(),
        }
        self.log.debug('request to the admin page of ticket_template. '
                       'category: %s, page: %s, path_info: %s', category, page, path_info)
        if req.method == 'POST':
            tid = data['id']
            if not tid:
                add_warning(req, _('ID is required.'))
            elif not re.match(r'^[\w\-]+$', tid):
                add_warning(req, _('ID contains invalid character(s).'))
            elif req.args.get('save') or req.args.get('update'):
                template_path = os.path.join(self.env.path, 'htdocs', 'ticket_templates', tid)
                with open(template_path, 'w') as fd:
                    fd.write(data['template'])
                section = self.config['ticket-template']
                section.set(tid, data['enabled'] and 'enabled' or 'disabled')
                section.set(tid + '.name', data['name'])
                section.set(tid + '.description', data['description'])
                section.set(tid + '.field_name', data['field_name'])
                section.set(tid + '.field_value', data['field_value'])
                section.set(tid + '.file', template_path)
                self.config.save()
                add_notice(req, _('Your changes have been saves.'))
            elif req.args.get('remove'):
                template_path = self.config.get('ticket-template', tid + '.file')
                if template_path and os.path.exists(template_path):
                    os.remove(template_path)
                for i, suffix in ('', '.name', '.description', '.field_name', '.field_value', '.file'):
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
        add_stylesheet(req, 'common/css/wiki.css')
        Chrome(self.env).add_wiki_toolbars(req)
        return 'admin_ticket_template.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        dirs = resource_filename(__name__, 'templates')
        self.log.debug('templates dirs: %s', dirs)
        return [dirs]

    def get_htdocs_dirs(self):
        htdocs = resource_filename(__name__, 'htdocs')
        self.log.debug('templates dirs: %s', htdocs)
        return [('ticket_template', htdocs)]

    # other methods
    def get_ticket_fields(self):
        fields = TicketSystem(self.env).get_ticket_fields()
        self.log.debug('ticket fields: %s', fields)
        return fields
