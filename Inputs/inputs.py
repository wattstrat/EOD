#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
from DB.Mongo.Mongo import Mongo


class Inputs(object):
    """
            This class is inherited by all input classes.
            Those classes can represent a csv, xml, html or text files...
    """

    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__()
        # New connection pool to mongo
        self._mongo = Mongo()
