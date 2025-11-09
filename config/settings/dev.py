from .base import *

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
# Default DB is SQLite via base.py; no change needed for now