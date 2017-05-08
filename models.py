import datetime

from google.appengine.ext import db

class Doorbell(db.Model):
    creation = db.DateTimeProperty(auto_now_add=True)
    rings = db.ListProperty(datetime.datetime)
    name = db.StringProperty()
    viewed = db.BooleanProperty()
    clientIDs = db.StringListProperty()