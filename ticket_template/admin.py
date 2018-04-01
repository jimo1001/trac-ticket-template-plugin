# -*- coding: utf-8 -*-
import os
import re

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.util.translation import domain_functions
from trac.web.chrome import add_notice, add_warning, add_script, add_stylesheet, add_script_data

gettext, _, tag_, N_, add_domain = domain_functions('tickettemplate', 'gettext', '_', 'tag_', 'N_', 'add_domain')


class TicketTemplateAdmin(Component):

    implements(IAdminPanelProvider, IPermissionRequestor)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('ticket', _("Ticket System"), 'templates', _("Ticket Template"))

    def render_admin_panel(self, req, cat, page, path_info):
        pass

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TRAC_ADMIN'

    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'field_name': '',
            'field_value': '',
            'template': '',
        }
        self.log.debug('request to ticket_template admin. cat: %s, page: %s, path_info: %s', cat, page, path_info)
        data['enable'] = self.config.getbool('theme', 'enable_css', False)
        if page == 'advanced':
            data.update({
                'template': req.args.get('js', ''),
                'id': req.args.get('custom_theme_id', ''),
                'regex': req.args.get('custom_theme_regex', ''),
                'enable': req.args.get('custom_theme_enabled', ''),
            })
        if req.method == 'POST':
            if page == 'advanced':
                name = req.args.get('custom_theme_id', '')
                regex = req.args.get('custom_theme_regex', '')
                enabled = req.args.get('custom_theme_enabled', '0')
                if not name:
                    add_warning(req, _('Name is required.'))
                elif not re.match(r'^[\w\-]+$', name):
                    add_warning(req, _('Name contains invalid character(s).'))
                elif req.args.get('update'):
                    if name == 'common':
                        css_file = open(os.path.join(self.env.path, 'htdocs', 'theme.css'), 'w')
                        css_file.write(req.args.get('css', ''))
                        css_file.close()
                        js_file = open(os.path.join(self.env.path, 'htdocs', 'theme.js'), 'w')
                        js_file.write(req.args.get('js', ''))
                        js_file.close()
                        self.config.set('theme', 'enable_css', enabled == '1' and 'enabled' or 'disabled')
                        self.config.set('theme', 'enable_js', enabled == '1' and 'enabled' or 'disabled')
                        self.config.save()
                        add_notice(req, _('Your changes have been saves.'))
                    else:
                        if not regex:
                            add_warning(req, _('Path(regex) is required.'))
                        else:
                            is_valid_regexp = False
                            try:
                                # check regexp
                                re.match(regex, '/dummy')
                                is_valid_regexp = True
                            except Exception, err:
                                self.log.info('Invalid regexp: %r. error: %s', regex, err)
                                add_warning(req, _('Path(regex) is invalid format.'))
                            if is_valid_regexp:
                                _dir = os.path.join(self.env.path, 'htdocs/_theme')
                                if not os.path.exists(_dir):
                                    os.mkdir(_dir)
                                js_file = open(os.path.join(_dir, name + '.js'), 'w')
                                js_file.write(req.args.get('js', ''))
                                js_file.close()
                                css_file = open(os.path.join(_dir, name + '.css'), 'w')
                                css_file.write(req.args.get('css', ''))
                                css_file.close()
                                self.config.set('theme-custom', name, enabled == '1' and 'enabled' or 'disabled')
                                self.config.set('theme-custom', name + '.regex', regex)
                                self.config.save()
                                add_notice(req, _('Your changes have been saves.'))
                elif req.args.get('remove'):
                    if name == 'common':
                        os.remove(os.path.join(self.env.path, 'htdocs', 'theme.js'))
                        os.remove(os.path.join(self.env.path, 'htdocs', 'theme.css'))
                        self.config.remove('theme', 'enable_css')
                        self.config.remove('theme', 'enable_js')
                    elif regex:
                        os.remove(os.path.join(self.env.path, 'htdocs/_theme', name + '.js'))
                        os.remove(os.path.join(self.env.path, 'htdocs/_theme', name + '.css'))
                        self.config.remove('theme-custom', name)
                        self.config.remove('theme-custom', name + '.regex')
                    self.config.save()
                    add_notice(req, _('Your changes have been saves.'))
                    data.update({
                        'css': '',
                        'js': '',
                        'id': '',
                        'regex': '',
                        'enable': '',
                    })

            # Simple Customize
            else:
                for key, value in self.config.options('theme'):
                    if key.startswith('color.'):
                        self.config.remove('theme', key)
                if 'enable_css' in req.args:
                    self.config.set('theme', 'enable_css', 'enabled')
                    self.config.set('theme', 'enable_js', 'enabled')
                else:
                    self.config.set('theme', 'enable_css', 'disabled')
                    self.config.set('theme', 'enable_js', 'disabled')
                f = open(os.path.join(self.env.path, 'htdocs', 'theme.css'), 'w')
                f.close()
                self.config.save()
                add_notice(req, _('Your changes have been saves.'))

        data['conditions'] = {
            'common': {
                'enabled': self.config.getbool('theme', 'enable_css', False)
            }
        }
        config = self.config['theme-custom']
        options = [(option.replace('.regex', ''), value) for option, value in config.options() if option.endswith('.regex')]
        for option, regex in options:
            data['conditions'][option] = {
                'regex': regex,
                'enabled': config.getbool(option)
            }
        data['base_url'] = self.env.base_url.rstrip('/')
        add_script_data(req, {
            'chrome_site_base_url': self.env.abs_href('/chrome/site'),
            'custom_theme_conditions': data['conditions'],
        })
        add_stylesheet(req, 'themeengine/farbtastic/farbtastic.css')
        add_stylesheet(req, 'themeengine/admin.css')
        add_script(req, 'themeengine/farbtastic/farbtastic.js')
        add_script(req, 'themeengine/jquery.rule.js')
        return 'admin_ticket_template.html', data
