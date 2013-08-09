#!/usr/bin/env python

import ConfigParser


class OpenINI:

    def __init__(self, config):
        self.config = config
        self._load()


    def _load(self):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read( self.config )


    def get(self, catalog, key, default=None):

        if self.cf.has_option(catalog, key):
            return self.cf.get(catalog, key)
        else:
            return default


    def get2(self, catalog, key, default=None):
        self._load()
        return self.get(catalog, key, default)


    def set(self, catalog, key, value):

        if not self.cf.has_section( catalog ):
            self.cf.add_section( catalog )
        return self.cf.set(catalog, key, value)


    def set2(self, catalog, key, value):
        self._load()
        return self.cf.set(catalog, key, value)


    def save(self):
        self.cf.write( open( self.config, 'w' ) )
