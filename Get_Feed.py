import feedparser
from soco import SoCo

def UhhYeahDude():
	d = feedparser.parse('http://uhhyeahdude.com/podcast/')
	return d.entries[0].links[0].href

if __name__ == '__main__':
    sonos = SoCo('192.168.1.101') # Pass in the IP of your Sonos speaker
    # You could use the discover function instead, if you don't know the IP

    # Pass in a URI to a media file to have it streamed through the Sonos
    # speaker
    sonos.play_uri(UhhYeahDude())

    track = sonos.get_current_track_info()

    print track['title']

    sonos.pause()

    # Play a stopped or paused track
    sonos.play()
