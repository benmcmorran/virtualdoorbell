import datetime
import os
import random
import urllib
import logging

from google.appengine.api import channel
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from models import Doorbell

def generateRandomID(length):
    # Generate a random identifier using characters from alphabet.
    # This is not guaranteed to be unique, but expected usage is
    # low enough to make the chance of a name conflict very low.
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    id = ''
    for i in range(length):
        id = id + alphabet[random.randint(0, 25)]
    return id

class Home(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'home.html')
        self.response.out.write(template.render(path, None))

class Create(webapp.RequestHandler):
    def post(self):
        key_name = generateRandomID(10)
        doorbell = Doorbell(key_name=key_name, name=self.request.get('doorbellName'), viewed=False)
        doorbell.put();
        self.redirect("/view/" + key_name);
    
class DoorbellHandler(webapp.RequestHandler):
    def get(self, key_name):
        doorbell = Doorbell.get_by_key_name(key_name);
        if doorbell:
            self.handleDoorbell(doorbell)
        else:
            self.error404()
    def handleDoorbell(self, doorbell):
        pass
    def doorbellName(self, doorbell):
        if doorbell.name:
            return doorbell.name
        else:
            return 'Doorbell ' + doorbell.key().name()
    def error404(self):
        self.error(404)
        path = os.path.join(os.path.dirname(__file__), 'error404.html')
        self.response.out.write(template.render(path, None))

class View(DoorbellHandler):
    def handleDoorbell(self, doorbell):
        clientID = doorbell.key().name() + generateRandomID(10)
        token = channel.create_channel(clientID)
        template_values = {
            'token': token,
            'key_name': doorbell.key().name(),
            'name': self.doorbellName(doorbell),
            'first_view': not doorbell.viewed }
        if (not doorbell.viewed):
            doorbell.viewed = True
            doorbell.put()
        path = os.path.join(os.path.dirname(__file__), 'view.html')
        self.response.out.write(template.render(path, template_values))
        
class ViewerConnected(webapp.RequestHandler):
    def post(self):
        logging.info('ViewerConnected')
        clientID = self.request.get('from')
        key_name = clientID[:10]
        doorbell = Doorbell.get_by_key_name(key_name)
        if doorbell:
            doorbell.clientIDs.append(clientID)
            doorbell.put()
            
class ViewerDisconnected(webapp.RequestHandler):
    def post(self):
        clientID = self.request.get('from')
        key_name = clientID[:10]
        doorbell = Doorbell.get_by_key_name(key_name)
        if doorbell and (clientID in doorbell.clientIDs):
            doorbell.clientIDs.remove(clientID)
            doorbell.put()

class Ring(DoorbellHandler):
    def handleDoorbell(self, doorbell):
        doorbell.rings.append(datetime.datetime.utcnow())
        doorbell.put();
        for clientID in doorbell.clientIDs:
            channel.send_message(clientID, '{ "event": "ring" }')
        template_values = { 'name': self.doorbellName(doorbell) }
        path = os.path.join(os.path.dirname(__file__), 'ring.html');
        self.response.out.write(template.render(path, template_values))

class Print(DoorbellHandler):
    def handleDoorbell(self, doorbell):
        template_values = {
            'key_name': doorbell.key().name(),
            'name': self.doorbellName(doorbell) }
        path = os.path.join(os.path.dirname(__file__), 'print.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication([
    ('/', Home),
    ('/create', Create),
    ('/_ah/channel/connected/', ViewerConnected),
    ('/_ah/channel/disconnected/', ViewerDisconnected),
    ('/view/(.*)', View),
    ('/print/(.*)', Print),
    ('/(.*)', Ring)
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()