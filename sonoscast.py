from flask import Flask,render_template, request
import feedparser
from datetime import datetime
from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil import parser
from soco import SoCo
import random
import pytz
import time

import sys

app = Flask(__name__)
app.config.from_pyfile('pod_db.cfg')
global db
db = SQLAlchemy(app)

@app.route('/add_new',methods = ['GET'])  
def add_new():
    return render_template('add_new.html')

@app.route('/find_rss', methods = ['POST'])
def find_rss():
	submit_rss = request.form['RSS_url']
	d = feedparser.parse(submit_rss)
	cast_name = d['feed']['title']
	cast_desc = d.feed.subtitle
	return render_template('rss_response.html', feed_address=submit_rss,rss_cast_title=cast_name,rss_cast_desc=cast_desc)

@app.route('/add_podcast',methods = ['POST'])
def add_podcast():
    submit_rss_final = request.form['RSS_url_final']
    #d = feedparser.parse(submit_rss_final)
    d = feedparser.parse(submit_rss_final)
    podfeed_new = pod(request.form['title_final'], request.form['RSS_url_final'],parser.parse(d['entries'][0]['published']))
    db.session.add(podfeed_new)
    db.session.commit()
    submit_rss_final = request.form['RSS_url_final']
    
    episode_count = len(d['entries'])

    #add error check for feeds that have 2 levels of links.
    for x in range(int(episode_count)):
        entry_new=episode(d['entries'][x]['title'],parser.parse(d.entries[x].published),podfeed_new.id,d.entries[x].enclosures[0].href)
        
        db.session.add(entry_new)
        db.session.commit()
    return redirect(url_for('show_all'))
   

@app.route('/')  
def show_all():
    return render_template('show_all.html', podcast_write=pod.query.order_by(pod.id.desc()).all())


#NOTE: Restrict with print len(d['entries']) also see feed.modified or in this case d.modified
@app.route('/episodes/<pod_id>/')  
def episodes(pod_id):
    ep_list = episode.query.filter_by(pod_id=pod_id).order_by(episode.pub_date.desc()).all()
    #replace this with a query.
    
    return render_template('episodes.html', ep_list=ep_list)

@app.route('/episodes/<pod_id>/<ep_id>')
#make sure to set l_date (listen date)
def play_ep(pod_id,ep_id):
    sonos = SoCo('192.168.1.136')
    play_ep = episode.query.filter_by(id=ep_id).first()
    print play_ep.ep_location
    sonos.play_uri(play_ep.ep_location)
    

@app.route('/random/<pod_id>/')
def get_random(pod_id):
    found = False
    while not found:

        random_selection = random.choice(episode.query.filter_by(pod_id=pod_id).order_by(episode.pub_date.desc()).all())
        print(random_selection)
    
        if random_selection.listened == False:
            found = True

    succ_response = {"pod_id": random_selection.pod_id, "title": random_selection.title, "location": random_selection.ep_location}
    random_selection.listened = True
    db.session.commit()

    return jsonify(succ_response)

@app.route('/update/<pod_id>/')
def update_pod(pod_id):
    the_pod = pod.query.filter_by(id=pod_id).first()
    d = feedparser.parse(the_pod.address)
    #fix time naivete
    utc = pytz.UTC
    last_update = (the_pod.update_date) 
  
    last_update = last_update.replace(tzinfo=None)
    
    current_update = parser.parse(d['entries'][0]['published'],ignoretz=True)
   
    #current_update = current_update.replace(tzinfo=utc)
    #current_update = current_update.replace(tzinfo=utc)
    print(last_update.tzinfo)
    print(current_update.tzinfo)
    update_response = False

    if last_update < current_update:
        print('True2')
        the_pod.update_date = parser.parse(d['entries'][0]['published'],ignoretz=True)
        print('True 3') 
        db.session.commit()
        print('True 3') 
        update_response = True

        feed_titles = []

        
        episode_count = len(d['entries'])
        print('True 2')   
        for x in range(int(episode_count)):
            current_entry = d['entries'][x]['title']
            feed_titles.append(current_entry)
            if_exists = db.session.query(episode.query.filter_by(title=current_entry).exists()).scalar()
            print(if_exists)

            if not (if_exists == True):
                entry_new=episode(d['entries'][x]['title'],parser.parse(d.entries[x].published),the_pod.id,d.entries[x].links[0].href)
                db.session.add(entry_new)
                db.session.commit()
        trim_these = episode.query.filter_by(pod_id=pod_id).all()
    
        episode_count = (len(trim_these))
        for x in range(int(episode_count)):
            if trim_these[x].title not in feed_titles:
                #print(trim_these[x].title)
                db.session.delete(trim_these[x])
                db.session.commit()
                #print('deleted')

            #add statement to delete


    return redirect(url_for('show_all'))


def start_over():
    db.reflect()
    db.drop_all()


#CLASSES
###################################################

#pod class need "LAST MODIFIED" from RSS Feed.
class pod(db.Model):
    __tablename__ = 'pods'
    id = db.Column('pod_id', db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    address = db.Column(db.String)
    add_date = db.Column(db.DateTime)
    update_date = db.Column(db.DateTime)
    addresses = db.relationship('episode',backref='pod',lazy=True)


    def __init__(self, title, address, update_date):
        self.title = title
        self.address = address
        self.add_date = datetime.utcnow()
        self.update_date = update_date

class episode(db.Model):
    __tablename__ = 'episodes'
    id = db.Column('episode_id', db.Integer, primary_key=True)
    title = db.Column(db.String)
    pub_date = db.Column(db.DateTime)
    l_date = db.Column(db.DateTime)
    pod_id = db.Column(db.Integer,db.ForeignKey(pod.id),nullable=False)
    ep_location = (db.Column(db.String))
    listened = (db.Column(db.Boolean))

    def __str__(self):
        return "Ep - id %s, Title %s, State %s" % (self.id, self.title, self.listened)

    def __init__(self, title, pub_date, pod_id,ep_location):
        self.title = title
        self.pub_date = pub_date
        self.pod_id = pod_id
        self.ep_location = ep_location
        self.listened = False

#########################################################
if __name__ == "__main__":
    
    #start_over()
    db.create_all()
    
    app.run()

