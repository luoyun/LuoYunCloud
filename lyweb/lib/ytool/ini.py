#!/usr/bin/env python

import ConfigParser

class ConfigINI:

    def __init__(self, config, catalog=None):
        self.config = config
        self._load()
        self.catalog = catalog


    def _load(self):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read( self.config )


    def set_catalog(self, catalog):
        self.catalog = catalog


    def get(self, key, default=None, catalog=None):

        if not catalog:
            if self.catalog:
                catalog = self.catalog
            else:
                return False

        if self.cf.has_option(catalog, key):
            return self.cf.get(catalog, key)
        else:
            return default


    def get2(self, key, default=None, catalog=None):
        self._load()
        return self.get(catalog, key, default)


    def set(self, key, value, catalog=None):

        if not catalog:
            if self.catalog:
                catalog = self.catalog
            else:
                return False

        if not self.cf.has_section( catalog ):
            self.cf.add_section( catalog )
        return self.cf.set(catalog, key, value)


    def set2(self, key, value, catalog=None):
        self._load()
        return self.cf.set(key, value, catalog)


    def save(self):
        self.cf.write( open( self.config, 'w' ) )
