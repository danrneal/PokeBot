#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time

log = logging.getLogger('Alarm')
args = get_args()


class Alarm(object):

    _defaults = {"pokemon": {}}

    @staticmethod
    def replace(string, pkinfo):
        if string is None:
            return None
        for key in pkinfo:
            string = string.replace("<{}>".format(key), str(pkinfo[key]))
        return string

    @staticmethod
    def try_sending(log, name, send_alert, args, max_attempts=3):
        for i in range(max_attempts):
            try:
                send_alert(**args)
                return
            except Exception as e:
                log.error((
                    "Encountered error while sending notification ({}: {})"
                ).format(type(e).__name__, e))
                log.error((
                    "{} is having connection issues. {} attempt of {}."
                ).format(name, i+1, max_attempts))
                time.sleep(3)
        log.error("Could not send notification... Giving up.")
