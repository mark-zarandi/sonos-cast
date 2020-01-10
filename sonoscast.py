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
import subprocess
import pytz
import time
import hjson
import json
import threading
from flask_bootstrap import Bootstrap
import sys
import ast
from flask_script import Manager, Server
from collections import OrderedDict
import logging
from pprint import pprint
from flask_socketio import SocketIO, send, emit


def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]


#######   FLASK SETUP    #############
app = Flask(__name__)
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.config.from_pyfile('pod_db.cfg')
global db
db = SQLAlchemy(app)
socketio = SocketIO(app)



@app.route('/add_new',methods = ['GET'])  
def add_new():
    return render_template('add_new.html')

@app.route('/recent/<pod_id>',methods = ['GET'])
def get_recent(pod_id):
    set_pod = pod.query.filter(pod.id == pod_id).first()
    d = feedparser.parse(set_pod.address)
    most_recent = d.entries[0].enclosures[0].href
    succ_response = {"pod_id": set_pod. id, "location": most_recent}
    return jsonify(succ_response)

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

@app.route('/settings/<pod_id>',methods = ['GET'])
#initiate settings view
def change_set(pod_id):
    set_pod = pod.query.filter(pod.id == pod_id).first()
    set_but = ast.literal_eval(set_pod.buttons)
    set_cond = True
    return render_template('app.html',podcast_write=pod.query.order_by(pod.id.desc()).all(),settings_pod = set_pod, set_lines = json.loads(set_pod.disp_title), set_buttons = set_but, settings_cond = set_cond)

@app.route('/save_settings',methods = ['POST','GET'])
#initiate settings view
def save_set():
    if request.method == 'POST':
        regular = True
        x = pod.query.get(request.form['podid'])
        new_disp = {}
        new_disp[0] = request.form['line1']
        if request.form['submit'] == 'regular':
            new_disp[1] = request.form['line2']
        else:
            new_disp[1] = ""
            regular = False
        x.disp_title = json.dumps(new_disp)
        db.session.commit()
        update_hjson()
        if regular:
            return render_template('app.html', podcast_write=pod.query.order_by(pod.id.desc()).all())
        else:
            return change_set(request.form['podid'])
    elif request.method == 'GET':
        if request.args.get('look') == 'delete':
            return del_podcast(request.args.get('podid'))

@app.route('/find_rss', methods = ['POST'])
def find_rss():
    show_modal = True
    try:
        submit_rss = request.form['RSS_url']
        d = feedparser.parse(submit_rss)
        cast_name = d['feed']['title']
        cast_desc = d.feed.subtitle
        show_modal = True
    except:
        rss_error = True
        return render_template('app.html',modal_cond = show_modal,rss_err=rss_error)
    return render_template('app.html', feed_address=submit_rss,rss_cast_title=cast_name,rss_cast_desc=cast_desc,modal_cond=show_modal)

def make_disp_title(working):
    return_word = {}
    working.replace(":","").replace(",","").replace("'","")
    start_w = working.split(" ")
    #only 2 lines
    for i in range(2):
        if len(start_w[i]) <= 7:
            return_word[i] = start_w[i]
        else:
            return_word[i] = left(start_w[i],7)
    return return_word



@app.route('/add_podcast',methods = ['POST'])
def add_podcast():
    submit_rss_final = request.form['RSS_url_final']
    #d = feedparser.parse(submit_rss_final)
    d = feedparser.parse(submit_rss_final)

    podfeed_new = pod(d['feed']['title'], request.form['RSS_url_final'],parser.parse(d['entries'][0]['published']),json.dumps(make_disp_title(d['feed']['title'])))
    db.session.add(podfeed_new)
    db.session.commit()
    submit_rss_final = request.form['RSS_url_final']
    
    episode_count = len(d['entries'])

    #add error check for feeds that have 2 levels of links.
    for x in range(int(episode_count)):
        entry_new=episode(d['entries'][x]['title'],parser.parse(d.entries[x].published),podfeed_new.id,d.entries[x].enclosures[0].href)
        
        db.session.add(entry_new)
        db.session.commit()
    update_hjson()
    return redirect(url_for('show_all'))

@app.route('/delete/<pod_id>')
def del_podcast(pod_id):
    pod.query.filter(pod.id == pod_id).delete()
    episode.query.filter(episode.pod_id == pod_id).delete()
    db.session.commit()
    filler_pod = db.session.query(pod).first()
    if filler_pod != None:
        ep_list = episode.query.filter_by(pod_id=filler_pod.id).order_by(episode.pub_date.desc()).all()
        return render_template('app.html', ep_list=ep_list,podcast_write=pod.query.order_by(pod.id.desc()).all())
    #consider putting a modal to confirm deletion.
    update_hjson()
    return render_template('app.html', podcast_write=pod.query.order_by(pod.id.desc()).all())

@app.route('/')  
def show_all():
    socketio.emit('message', {'data': 'Connected'})
    return render_template('app.html', podcast_write=pod.query.order_by(pod.id.desc()).all())

@app.route('/fix_disp/')
def fix_disp_title():
    pod_list = pod.query.order_by(pod.id.desc()).all()

    for pod in pod_list:
        pod.disp_title = json.dumps(make_disp_title(pod.title))
        db.session.commit()
    return render_template('app.html', podcast_write=pod.query.order_by(pod.id.desc()).all())

#NOTE: Restrict with print len(d['entries']) also see feed.modified or in this case d.modified
@app.route('/episodes/<pod_id>/')  
def episodes(pod_id):
    ep_list = episode.query.filter_by(pod_id=pod_id).order_by(episode.pub_date.desc()).all()
    #replace this with a query.
    
    return render_template('app.html', ep_list=ep_list,podcast_write=pod.query.order_by(pod.id.desc()).all())

@app.route('/episodes/<pod_id>/<ep_id>')
#make sure to set l_date (listen date)
def play_ep(pod_id,ep_id):
    sonos = SoCo('192.168.1.136')
    play_ep = episode.query.filter_by(id=ep_id).first()
    print(play_ep.ep_location)
    sonos.play_uri(play_ep.ep_location)

@app.route('/update/<pod_id>/')
def update_pod(pod_id):
    the_pod = pod.query.filter_by(id=pod_id).first()
    d = feedparser.parse(the_pod.address)
    #fix time naivete
    utc = pytz.UTC
    last_update = (the_pod.update_date) 
  
    last_update = last_update.replace(tzinfo=None)
    
    current_update = parser.parse(d['entries'][0]['published'],ignoretz=True)
   

    update_response = False

    if last_update < current_update:
   
        the_pod.update_date = parser.parse(d['entries'][0]['published'],ignoretz=True)

        db.session.commit()

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


@app.route('/write_hjson/')
def update_hjson():

    def conc_disp(json_disp):
        print(json_disp)
        if len(json_disp) == 1:
            return_word = str(json_disp['0'])
        else:
            return_word = str(json_disp['0']) + " " + str(json_disp['1'])
        return return_word 


    text_file = open("../Au/buttons.hjson", "w")
    podcast_write=pod.query.order_by(pod.id.desc()).all()
    pod_list_dict = OrderedDict()
    for look_pod in podcast_write:
        new_title = look_pod.title.replace(":","").replace(",","").replace(" ","_")
        display_this = conc_disp(json.loads(look_pod.disp_title))
        pod_list_dict.update({new_title:{'label':display_this,'method':["get_recent","get_random"],'pod_id':look_pod.id}})
    n = text_file.write("{Pods:" + hjson.dumps(pod_list_dict)+"}")
    #note: auto discover room info.
    #temp_rooms_dict = {'Rooms':
    #{
    #'Lib':'192.168.1.136'
    #'Kitch':'192.168.1.145'
    #'Master':'192.168.1.101'
    #'Living':'192.168.1.116'
    #}}
    socketio.emit('message', {'data': 'Connected'})
    return redirect(url_for('show_all'))


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
    disp_title = db.Column(db.String(100))
    buttons = db.Column(db.String(100))

    def __init__(self, title, address, update_date,disp_title):
        self.title = title
        self.address = address
        self.add_date = datetime.utcnow()
        self.update_date = update_date
        self.disp_title = disp_title
        self.buttons = "{'method':['1','2']}"
        #use ast to interpret

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
    
    bootstrap = Bootstrap(app)
    #app.logger.disabled = True
    #log = logging.getLogger('werkzeug')
    #log.disabled = True
    socketio.run(app,host="0.0.0.0")
    
