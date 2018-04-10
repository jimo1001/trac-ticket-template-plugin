#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup

extra = {}

try:
    import babel
    from trac.dist import get_l10n_js_cmdclass
except ImportError:
    babel = None
else:
    extra['cmdclass'] = get_l10n_js_cmdclass()
    extractors = [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'genshi', None),
        ('**/templates/**.txt', 'genshi',
         {'template_class': 'genshi.template:NewTextTemplate'}),
    ]
    extra['message_extractors'] = {
        'ticket_template': extractors,
    }

setup(
    name='TracTicketTemplate',
    description="Ticket Template Plugin for Trac.",
    version='0.1',
    packages=['ticket_template'],
    package_data={'ticket_template': [
        '*.txt',
        'templates/*.*',
        'htdocs/*.*',
        'tests/*.*',
        'locale/*.*',
        'locale/*/LC_MESSAGES/*.*',
    ]},
    author="Yoshinobu Fujimoto",
    author_email='yosinobu@iij.ad.jp',
    license="MIT",
    keywords="trac ticket template",
    url="https://gh.iiji.jp/idp/trac-ticket-template-plugin",
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac', 'simple_json' if sys.version_info < (2, 6) else ''],
    test_suite='ticket_template.tests',
    entry_points={
        'trac.plugins': [
            'ticket_template.admin = ticket_template.admin',
            'ticket_template.web_api = ticket_template.web_api',
        ],
    },
    **extra
)
