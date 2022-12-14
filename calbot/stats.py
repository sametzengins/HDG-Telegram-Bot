# -*- coding: utf-8 -*-

# Copyright 2016 Denis Nelubin.
#
# This file is part of Calendar Bot.
#
# Calendar Bot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Calendar Bot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Calendar Bot.  If not, see http://www.gnu.org/licenses/.

import os
import datetime
import logging
from configparser import ConfigParser

from calbot.conf import ConfigFile


__all__ = ['update_stats', 'get_stats']

logger = logging.getLogger('stats')

STATS_MESSAGE_FORMAT="""Active users: {}
Active calendars: {}
Disabled calendars: {}
Notified events: {}
Last calendars processed:
{} - {}"""


def update_stats(config):
    """
    Updates statistics.
    :param config: Main config object
    :return: None
    """
    try:
        config_file = StatsConfigFile(config.vardir)
        parser = ConfigParser(interpolation=None)
        parser.add_section('stats')

        users = 0
        calendars = 0
        disabled_calendars = 0
        events = 0
        last_process_min = datetime.datetime.utcnow().isoformat()
        last_process_max = datetime.datetime.utcfromtimestamp(0).isoformat()

        for name in os.listdir(config.vardir):
            if os.path.isdir(os.path.join(config.vardir, name)):
                users += 1
                user_id = name
                for calendar in config.load_calendars(user_id):
                    if calendar.enabled:
                        calendars += 1
                        last_process_min = min(calendar.last_process_at or last_process_min, last_process_min)
                        last_process_max = max(calendar.last_process_at or last_process_max, last_process_max)
                        calendar.load_events()
                        events += len(calendar.events)
                    else:
                        disabled_calendars += 1

        parser.set('stats', 'users', str(users))
        parser.set('stats', 'calendars', str(calendars))
        parser.set('stats', 'disabled_calendars', str(disabled_calendars))
        parser.set('stats', 'events', str(events))
        parser.set('stats', 'last_process_min', last_process_min)
        parser.set('stats', 'last_process_max', last_process_max)

        config_file.write(parser)
    except Exception as e:
        logger.warning('Failed to update stats', exc_info=True)


def get_stats(config):
    """
    Reads stats object from the stats.cfg file
    :param config: Main Config object
    :return: Stats object
    """
    config_file = StatsConfigFile(config.vardir)
    return Stats.load(config_file)


class Stats:
    """
    Holds statistics data.
    """

    def __init__(self, **kwargs):
        self.users = kwargs['users']
        """Number of active users"""
        self.calendars = kwargs['calendars']
        """Number of active calendars"""
        self.disabled_calendars = kwargs['disabled_calendars']
        """Number of disabled calendars"""
        self.events = kwargs['events']
        """Number of notified events"""
        self.last_process_min = kwargs['last_process_min']
        """Timestamp of the calendar processed, min value"""
        self.last_process_max = kwargs['last_process_max']
        """Timestamp of the calendar processed, max value"""

    @classmethod
    def load(cls, stats_config):
        """
        Loads stats from the stats.cfg file
        """
        parser = stats_config.read_parser()
        return cls(
            users=parser.getint('stats', 'users', fallback=0),
            calendars=parser.getint('stats', 'calendars', fallback=0),
            disabled_calendars=parser.getint('stats', 'disabled_calendars', fallback=0),
            events=parser.getint('stats', 'events', fallback=0),
            last_process_min=parser.get('stats', 'last_process_min', fallback=None),
            last_process_max=parser.get('stats', 'last_process_max', fallback=None)
        )

    def __str__(self):
        return STATS_MESSAGE_FORMAT.format(self.users,
                                           self.calendars,
                                           self.disabled_calendars,
                                           self.events,
                                           self.last_process_min,
                                           self.last_process_max)


class StatsConfigFile(ConfigFile):
    """
    Reads and writes stats config file.
    """

    def __init__(self, vardir):
        """
        Creates the config
        :param vardir: basic var dir
        """
        super().__init__(os.path.join(vardir, 'stats.cfg'))
