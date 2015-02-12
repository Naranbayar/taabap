# -*- coding: utf-8 -*-
"""
"""
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
import json
import urllib2
# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'a'

# create our little application :)
application = Flask(__name__)
application.config.from_object(__name__)
application.config.from_envvar('FLASKR_SETTINGS', silent=True)


def init_db():
    """Creates the database tables."""
    with application.app_context():
        db = get_db()
        with application.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context."""
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(application.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db


@application.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


@application.route('/')
def show_entries():
    db = get_db()
    if session.get('logged_in'):
        cur = db.execute('select id, origin, title, origin_url, content, time, image, read, published from news order by id desc')
    else:
        cur = db.execute('select id, origin, title, origin_url, content, time, image, read from news where published=1 order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@application.route('/news/<ids>')
def redirect_news(ids):
    db = get_db()
    cur = db.execute("select url, read from news where id="+ids)
    entries = cur.fetchall()
    redirect_url = entries[0]["url"]
    cnt_read = str(int(entries[0]["read"]) + 1)
    db.execute("update news SET read="+cnt_read+" WHERE id="+ids)
    db.commit()
    return redirect(redirect_url)

@application.route('/delete/<ids>')
def delete_news(ids):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute("delete from news where id="+ids)
    db.commit()
    return redirect(url_for('show_entries'))

@application.route('/publish/<ids>')
def publish_news(ids):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute("update news SET published=1 WHERE id="+ids)
    db.commit()
    return redirect(url_for('show_entries'))

@application.route('/unpublish/<ids>')
def unpublish_news(ids):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute("update news SET published=0 WHERE id="+ids)
    db.commit()
    return redirect(url_for('show_entries'))

@application.route('/delete_all', methods=['POST'])
def delete_all():
    if not session.get('logged_in'):
        abort(401)
    
    db = get_db()
    db.execute("delete from news where published=0")
    db.commit()
    return redirect(url_for('show_entries'))

@application.route('/add_news', methods=['POST'])
def add_news():
    if not session.get('logged_in'):
        abort(401)

    url = 'http://qlio-rss.appspot.com/'
    jsonData = json.loads(urllib2.urlopen(url).read())
    db = get_db()
    for item in jsonData:
        db.execute('insert into news (url, origin, title, origin_url, content, time, image, read, published) values (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [item.get("url"), item.get("origin"), item.get("title"), item.get("origin_url"), item.get("content"), item.get("time"), item.get("image"), 0, 0])

    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@application.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] != application.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    init_db()
    application.run(host='0.0.0.0')
