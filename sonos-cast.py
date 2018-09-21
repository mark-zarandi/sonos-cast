from flask import Flask,render_template, request
import feedparser
from datetime import datetime
from flask import Flask, request, flash, url_for, redirect, \
     render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('pod_db.cfg')
global db
db = SQLAlchemy(app)

@app.route('/')
def welcome():
    #db.create_all(). FIX THIS IT ONLY NEEDS TO BE RUN ONCE!
    return render_template('index.html')

@app.route('/find_rss', methods = ['POST'])
def find_rss():
	submit_rss = request.form['RSS_url']
	d = feedparser.parse(submit_rss)
	cast_name = d['feed']['title']
	cast_desc = d.feed.subtitle
	return render_template('rss_response.html', feed_address=submit_rss,rss_cast_title=cast_name,rss_cast_desc=cast_desc)

@app.route('/add_podcast',methods = ['POST'])
def add_podcast():
    #submit_rss_final = request.form['RSS_url_final']
    #d = feedparser.parse(submit_rss_final)
    podfeed_new = podfeed(request.form['title_final'], request.form['RSS_url_final'])
    db.session.add(podfeed_new)
    db.session.commit()
    flash(u'Podfeed item was successfully created.')
    return render_template('show_all.html')
   
@app.route('/show_all')   
def show_all():
    db = get_db()
    cur = db.execute('select title, from pods order by pod_id desc')
    podcast_list = cur.fetchall()
    return render_template('show_all.html', podcast_write=podcast_list)    

#start db programming
class podfeed(db.Model):
    __tablename__ = 'pods'
    id = db.Column('pod_id', db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    address = db.Column(db.String)
    add_date = db.Column(db.DateTime)

    def __init__(self, title, address):
        self.title = title
        self.address = address
        self.add_date = datetime.utcnow()

if __name__ == "__main__":
	app.run()

