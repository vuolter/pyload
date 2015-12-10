# -*- coding: utf-8 -*-
# @author: mkaay

import time

from pyload.utils import uniqify


class Pull_manager(object):

    def __init__(self, core):
        self.pyload = core
        self.clients = []


    def new_client(self, uuid):
        self.clients.append(Client(uuid))


    def clean(self):
        for n, client in enumerate(self.clients):
            if client.lastActive + 30 < time.time():
                del self.clients[n]


    def get_events(self, uuid):
        events = []
        validUuid = False
        for client in self.clients:
            if client.uuid == uuid:
                client.lastActive = time.time()
                validUuid = True
                while client.newEvents():
                    events.append(client.popEvent().toList())
                break
        if not validUuid:
            self.new_client(uuid)
            events = [ReloadAllEvent("queue").toList(), ReloadAllEvent("collector").toList()]
        return uniqify(events)


    def add_event(self, event):
        for client in self.clients:
            client.addEvent(event)


class Client(object):

    def __init__(self, uuid):
        self.uuid = uuid
        self.lastActive = time.time()
        self.events = []


    def new_events(self):
        return len(self.events) > 0


    def pop_event(self):
        if not len(self.events):
            return None
        return self.events.pop(0)


    def add_event(self, event):
        self.events.append(event)


class Update_event(object):

    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination


    def to_list(self):
        return ["update", self.destination, self.type, self.id]


class Remove_event(object):

    def __init__(self, itype, iid, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.destination = destination


    def to_list(self):
        return ["remove", self.destination, self.type, self.id]


class Insert_event(object):

    def __init__(self, itype, iid, after, destination):
        assert itype == "pack" or itype == "file"
        assert destination == "queue" or destination == "collector"
        self.type = itype
        self.id = iid
        self.after = after
        self.destination = destination


    def to_list(self):
        return ["insert", self.destination, self.type, self.id, self.after]


class Reload_all_event(object):

    def __init__(self, destination):
        assert destination == "queue" or destination == "collector"
        self.destination = destination


    def to_list(self):
        return ["reload", self.destination]


class Account_update_event(object):

    def to_list(self):
        return ["account"]


class Config_update_event(object):

    def to_list(self):
        return ["config"]
