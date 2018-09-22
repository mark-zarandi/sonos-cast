from flask_sqlalchemy import SQLAlchemy

db = None

def init_db(app):
	global db
	db = SQLAlchemy(app)
	
	from models import pod
    	print 'Recreating DB.'
    	db.create_all()
    	print 'All done.'

def clear_db(app):
	global db
	db = SQLAlchemy(app)
	db.reflect()
	db.clear_all()
