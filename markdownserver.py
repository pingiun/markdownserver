import os
import hashlib
import hmac
import hashlib
import json

import markdown
import git
import magic

from flask import Flask, request, Markup, Response, render_template

app = Flask(__name__)

app.config.from_envvar('MARKDOWNSERVER_SETTINGS')


@app.route('/_/githubwebhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        return 'Method Not Allowed', 405

    payload = json.loads(request.data.decode('utf-8'))

    if 'GITHUB_SHARED_SECRET' in app.config:
        if not request.headers.get('X-Hub-Signature'):
            return 'Unauthorized', 401
        hmacdigest = 'sha1=' + hmac.new(app.config['GITHUB_SHARED_SECRET'],
                              request.data, hashlib.sha1).hexdigest()
        if hmac.compare_digest(hmacdigest,
                               request.headers.get('X-Hub-Signature')) == False:
            return 'Unauthorized', 401

    if request.headers.get('X-GitHub-Event') == 'ping':
        return json.dumps({'msg': 'pong'})

    if request.headers.get('X-Github-Event') != 'push':
        return 'Bad Request', 400

    g = git.cmd.Git('templates')
    print(g.pull())
    return 'OK', 200


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
            return open(Cache.get_instance().get_file(path)).read()
        except FileNotFoundError:
            return 'Not found', 404
    else:
        try:

            def generate():
                with open(os.path.join('templates', path), 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            break
                        yield data

            mime = magic.Magic(mime=True)
            return Response(
                generate(),
                mimetype=mime.from_file(os.path.join('templates', path)))
        except FileNotFoundError:
            return 'Not found', 404


class Cache(object):

    _instance = None

    def __init__(self):
        self.hashes = dict()
        os.makedirs('cache', exist_ok=True)

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

    def get_file(self, path):
        with open(os.path.join('templates', path), 'rb') as file:
            filehash = Cache._get_hash(file)
        if path in self.hashes:
            if filehash == self.hashes[path]:  # File not changed
                return os.path.join('cache', path)

        with open(os.path.join('templates', path), 'r') as inputfile:
            content = Markup(markdown.markdown(inputfile.read()))
            with open(os.path.join('cache', path), 'w') as outputfile:
                outputfile.write(
                    render_template(
                        'template.html', content=content))
        self.hashes[path] = filehash
        return os.path.join('cache', path)
