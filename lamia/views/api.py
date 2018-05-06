from lamia import app
from lamia import sqla
from lamia.parsers import ForumPostParser
from collections import OrderedDict
from lamia.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, make_response, json, flash, session
from flask_login import login_user, logout_user, current_user, login_required
import arrow, time, math
from threading import Thread
import random
from lamia.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string, get_preview, CategoryPermissionCalculator, crossdomain
from lamia.views.dashboard import broadcast
import re, json
from datetime import datetime
import lamia.sqlmodels as sqlm
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import joinedload
from BeautifulSoup import BeautifulSoup
from sqlalchemy.sql import text
from lamia.utilities import render_lamia_template as render_template

@app.route('/api/version', methods=['GET'])
@crossdomain(origin="*")
def api_version():
    # request.headers["Origin"]
    return app.jsonify(version="Prerelease 4")
    
@app.route('/api/rss/comments', methods=['POST'])
@crossdomain(origin="*")
def rss_get_comments(key, entry):
    request_json = request.get_json(force=True)
    
    try:
        rss_feed = sqlm.RSSScraper.query.filter_by(rss_key=request_json.get(key, ""))[0]
    except IndexError:
        return app.jsonify(error="RSS Feed does not exist.")
    
    try:
        rss_content = sqlm.RSSContent.query.filter_by(remote_id=request_json.get(entry, ""))[0]
    except IndexError:
        return app.jsonify(error="RSS Content does not exist.")
        
    return app.jsonify(version="Prerelease 4")
    