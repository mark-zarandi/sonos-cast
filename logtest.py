import logging
from logging import handlers

level    = logging.INFO
format   = '%(asctime)s %(name)-8s %(levelname)-8s %(message)s'
handlers = [logging.handlers.TimedRotatingFileHandler('filename',when="D",interval=1,backupCount=5,encoding=None,delay=False,utc=False,atTime=None), logging.StreamHandler()]

logging.basicConfig(level = level, format = format, handlers = handlers)
logging.info('Hey, this is working!')
logging.warning('Hey, this is working!')