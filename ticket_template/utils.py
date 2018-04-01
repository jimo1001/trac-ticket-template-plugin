# -*- coding: utf-8 -*-
#

import calendar
import time


calendar.setfirstweekday(calendar.MONDAY)

SEC_PER_DAY = 60 * 60 * 24
SEC_PER_WEEK = 60 * 60 * 24 * 7

SYSTEM_USER = "SYSTEM"

DEFAULT_FORMAT = {
    "now": "%Y-%m-%d %H:%M:%S",
    "today": "%Y-%m-%d",
    "this_week": "%w",
    "this_month": "%m",
    "this_year": "%Y",
}


def formatField(config, tt_value, user, req_args):
    """ format field value
    """
    # generate format dict
    mapping = {}

    t = int(time.time())
    for k, v in DEFAULT_FORMAT.items():
        format = config.get('tickettemplate', k + '_format', v)
        mapping[k] = time.strftime(format, time.localtime(t))

    mapping['user'] = user

    mapping.update(req_args)

    try:
        return tt_value % mapping
    except:
        return tt_value
