import logging
import os


from flask import Flask


from .config import *
from . import app


def create_app():
    print('Creating app...')
    app = Flask(__name__)
    app.config.from_object(config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if __name__ == '__main__':
        app.run(host='localhost', port=5000)
  
    return app