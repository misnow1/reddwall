#!/usr/bin/env python
import logging
from logging.handlers import SysLogHandler
from optparse import OptionParser

from detools import imagefinder
from detools import wallpaper
import threading
import praw
import random
import os.path
import json

logger = logging.getLogger(__name__)

r = praw.Reddit(user_agent='mac:org.bauer.reddwall:v1.0.0 (by /u/mjbauer95)')

pasts = ['hour', 'day', 'week', 'month', 'year', 'all']
suggested_subreddits = ['wallpapers', 'wallpaper', 'EarthPorn',
                        'BackgroundArt', 'TripleScreenPlus', 'quotepaper',
                        'BigWallpapers', 'MultiWall', 'DesktopLego',
                        'VideoGameWallpapers']
select = ['random', 'top']

default_settings = {
    'interval': 24,
    'minVote': 0,
    'subreddit': 'wallpapers',
    'search': '',
    'past': 'day',
    'allowNSFW': False,
    'select': 'top'
}


class ReddWall(object):
    SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".reddwall.json")
    MIN_NUM = 1
    MAX_TRIES = 10
    submissions = []
    needSubmissionsUpdate = False
    is_running = False
    submission_ids = []
    settings = default_settings
    updatingSubmissions = False

    def __init__(self):
        try:
            os.stat('/var/run/syslog')
            syslog_socket = '/var/run/syslog'
        except OSError:
            syslog_socket = '/dev/log'

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%b %H:%M:%S')
        handler = SysLogHandler(address=syslog_socket,
                                facility=SysLogHandler.LOG_USER)
        formatter = logging.Formatter('fetch-alerts: %(message)s')
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.LoadSettings()

        # thread = threading.Thread(target=self.Init)
        # thread.setDaemon(True)
        # thread.start()

        self.SaveSettings()

    def SubmissionOkay(self, submission):
        return submission.score > self.settings['minVote'] and \
            (self.settings['allowNSFW'] or not submission.over_18) and \
            submission.id not in self.submission_ids

    def GetSubmissions(self, subreddit_name):
        # if self.updatingSubmissions:
        #    return
        logger.info("Updating submissions from /r/%s" % subreddit_name)

        self.updatingSubmissions = True
        subreddit = r.get_subreddit(subreddit_name)
        pasts = {
            'hour': subreddit.get_top_from_hour,
            'day': subreddit.get_top_from_day,
            'week': subreddit.get_top_from_week,
            'month': subreddit.get_top_from_month,
            'year': subreddit.get_top_from_year,
            'all': subreddit.get_top_from_all
        }

        self.submissions = []
        num_submissions = self.MIN_NUM
        limit = 100
        if self.settings['select'] == 'random':
            limit = 100
        elif self.settings['select'] == 'top':
            limit = 1
        request = pasts[self.settings['past']](limit=limit)
        for submission in request:
            if self.SubmissionOkay(submission):
                self.submissions.append(submission)
                # self.submission_ids.append(submission.id)
                num_submissions -= 1
        if self.settings['select'] == 'random':
            random.shuffle(self.submissions)
        self.needSubmissionsUpdate = False
        self.updatingSubmissions = False

    def UntilValidImageUrl(self, subreddit_name):
        tries = self.MAX_TRIES
        logger.info("Looking for images at most %d times" % tries)
        while tries > 0:
            try:
                submission = self.submissions.pop()
                logger.info("Attempting to get submission from %s" %
                            submission.url)
                return imagefinder.get_image_request(submission.url)
            except imagefinder.NoImageFound:
                tries -= 1
                pass

        raise imagefinder.NoImageFound(None)

    def NextWallpaper(self, subreddit_name):
        # if self.is_running:
        #    return
        if not subreddit_name:
            subreddit_name = self.settings['subreddit']

        self.is_running = True

        self.GetSubmissions(subreddit_name)
        url = self.UntilValidImageUrl(subreddit_name)
        wallpaper.set_wallpaper_request(url)
        self.is_running = False

    def StartTimer(self):
        self.timer.Start(self.settings['interval'] * 60 * 60 * 1000)

    def OnUpdateInterval(self):
        self.timer.Stop()
        self.StartTimer()

    def OnFilterUpdate(self):
        self.needSubmissionsUpdate = True

    def OSXIsGUIApplication(self):
        return False

    def SaveSettings(self):
        with open(self.SETTINGS_PATH, 'w') as outfile:
            json.dump(self.settings, outfile)

    def LoadSettings(self):
        try:
            with open(self.SETTINGS_PATH, 'r') as infile:
                self.settings.update(json.load(infile))
        except:
            pass


def main():
    r = ReddWall()

    usage = """%prog [options]"""
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--subreddit", dest="subreddit",
                      default=r.settings['subreddit'],
                      help="The subreddit to pull images from")
    (options, args) = parser.parse_args()

    r.NextWallpaper(options.subreddit)
