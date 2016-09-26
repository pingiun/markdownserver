import os
import hashlib

import markdown
from flask import Flask
from flask import Markup
from flask import render_template

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        path = 'index.md'
    split = path.split('.')
    if len(split) == 1:
        path += '.md'
        ext = 'md'
    else:
        ext = split[-1]

    if ext == 'md':
        try:
            return open(Cache.get_instance().get_file(app.config['SERVER_NAME'], path)).read()
        except FileNotFoundError:
            return 'Not found', 404
    else:
        try:
            with open(os.path.join('content', path), 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return 'Not found', 404

class Cache(object):

    _instance = None

    def __init__(self):
        self.hashes = dict()

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = Cache()
        return cls._instance

    @staticmethod
    def _get_hash(file):
        BUF_SIZE = 65536
        sha1 = hashlib.sha1()
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
        return sha1.digest()

    def get_file(self, base, path):
        with open(os.path.join(base, 'content', path), 'rb') as file:
            filehash = Cache._get_hash(file)
        if path in self.hashes:
            if filehash == self.hashes[path]: # File not changed
                return os.path.join(base, 'cache', path)
        
        with open(os.path.join(base, 'content', path), 'r') as inputfile:
            content = Markup(markdown.markdown(inputfile.read()))
            with open(os.path.join(base, 'cache', path), 'w') as outputfile:
                outputfile.write(render_template('template.html', content=content))
        self.hashes[path] = filehash
        return os.path.join(base, 'cache', path)
