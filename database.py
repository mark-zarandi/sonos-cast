from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, flash, url_for, redirect, render_template
app = Flask(__name__)
db = SQLAlchemy(app)

def init_db(app):
	global db
	
	db.init_app(app)
	db.create_all()
	db.session.commit()
	print 'All done.'
