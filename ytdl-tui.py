#!/usr/bin/env python
# encoding: utf-8

from subprocess import run
from subprocess import check_output
import json
import sys
import npyscreen

class Fmt(object):
    def __init__(self, fmtId, text):
        self.fmtId = fmtId
        self.text = text

class FmtList(npyscreen.SelectOne):
    def __init__(self, *args, **keywords):
        super(FmtList, self).__init__(*args, **keywords)

    def display_value(self, vl):
        return '{}'.format(vl.text)

class TestApp(npyscreen.NPSApp):
    audioFmts = []
    videoFmts = []
    url       = 'https://www.youtube.com/watch?v=2MpUj-Aua48'

    def getSizeString(self, kilobytes):
        unit = 'KiB'
        if kilobytes >= 1024:
            kilobytes = kilobytes / 1024
            unit = 'MiB'

        if kilobytes >= 1024:
            kilobytes = kilobytes / 1024
            unit = 'GiB'

        return '{}{}'.format( round(kilobytes, 2), unit )

    def appendFmtToList(self, lst, fmtId, description, bitrate, kilobytes):
        sizeString = self.getSizeString(kilobytes)
        s = '{}\t- {}\t{}kbps'.format(fmtId, description, bitrate).expandtabs(2)
        s = '{}\t{}'.format(s, sizeString).expandtabs(8)
        lst.append( Fmt(fmtId, s) )

    def downloadJson(self):
        if len(sys.argv) > 1:
            self.url = sys.argv[1]

        print( 'Querying formats for {}'.format(self.url) )
        result = check_output( [ 'youtube-dl -j {}'.format(self.url) ], shell=True ).decode('utf-8')
        #result = run( [ 'youtube-dl -j {}'.format(self.url) ], shell=True, capture_output=True, text=True )
        #j = json.loads(result.stdout)
        return json.loads(result)

    def fillModels(self):
        j = self.downloadJson()
        duration = j['duration']
        fmts = j['formats']

        for fmt in fmts:
            try:
                fmtId = fmt['format_id']
                size = fmt['filesize']
                kilobytes = size / 1024
                bitrate = round( (kilobytes / duration) * 8 )

                if fmt['vcodec'] and fmt['vcodec'] != 'none':
                    height = fmt['height']
                    desc = '{}p'.format(height)
                    self.appendFmtToList(self.videoFmts, fmtId, desc, bitrate, kilobytes)
                else:
                    acodec = fmt['acodec'][:4]
                    self.appendFmtToList(self.audioFmts, fmtId, acodec, bitrate, kilobytes)
            except KeyError as e:
                print('Unknown id/codec.')

    def main(self):
        self.fillModels()

        F  = npyscreen.Form(name = "Select preferred formats", minimum_lines=20)

        F.add(npyscreen.FixedText, value = "Video", max_width=40, editable=False)
        vidList = F.add(FmtList, value = [0], name="Video", max_width=40, max_height=16,
                values = self.videoFmts, scroll_exit=True, exit_right=True)

        F.add(npyscreen.FixedText, value = "Audio", max_width=40, editable=False, relx=42, rely=2)
        audList = F.add(FmtList, value = [0], name="Audio", max_width=40, max_height=16,
                values = self.audioFmts, scroll_exit=True, exit_left=True, relx=42, rely=3)

        #This lets the user interact with the Form.
        F.edit()

        import curses
        curses.endwin()

        ids = [ self.videoFmts[ vidList.value[0] ].fmtId, self.audioFmts[ audList.value[0] ].fmtId ]
        prefs = '{}+{}'.format( ids[0], ids[1]  )
        print(prefs)
        run( [ "mpv --term-status-msg='Video bitrate: ${{video-bitrate}}, audio bitrate: ${{audio-bitrate}}' --ytdl-format {} {}".format(prefs, self.url) ], shell=True )


if __name__ == "__main__":
    App = TestApp()
    App.run()
