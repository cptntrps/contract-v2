"""
Database package initialization
"""
from .database import db, init_app
from .models import *

__all__ = ['db', 'init_app']