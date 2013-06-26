# coding: utf-8

import random

valid_letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ\
abcdefghijklmnopqrstuvwxyz\
0123456789'

def randstring(length=10):
    L = [ random.choice(valid_letters) for i in xrange(length) ]
    return ''.join( L )

