import feedparser

def get_recent(rss_address):
	d = feedparser.parse(rss_address)
	return d.entries[0].enclosures[0].href

if __name__ == "__main__":
	podcast_address = 'https://www.npr.org/rss/podcast.php?id=500005'
	print(get_recent(podcast_address))