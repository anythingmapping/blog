from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, g
)

from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
import logging
import markdown
import os
from slugify import slugify


bp = Blueprint('blog', __name__)
logger = logging.getLogger('flaskr.blog')


UPLOAD_FOLDER = '/static/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

##### trying to build a landing page here
# @bp.route('/')
# def index():
#     return render_template('landing/landing.html')

@bp.route('/')
def blog():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, intro, slug, lng, lat, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/blog/<slug>')
def post_detail(slug):
    db = get_db()
    post = db.execute(
        'SELECT * FROM post WHERE slug = ?',
        (slug,)
    ).fetchone()
 
    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))
    
    return render_template('blog/post_detail.html', post=post)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        intro = request.form['intro']
        body = request.form['body']
        lng = request.form['lng']
        lat = request.form['lat']
        # file = request.files['file']
        slug = slugify(title)

        error = None

        logger.info("img dir:")
        logger.info(current_app.config['UPLOAD_FOLDER'])

        required = [title, intro, body, lng, lat]
        for i in required:
            if not i:
                error = f'{i} is required'
       
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, intro, body, lng, lat, author_id, slug)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (title, intro, body, lng, lat, g.user['id'], slug)
            )
            db.commit()
            return redirect(url_for('blog.blog'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, lng, lat, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        lng = request.form['lng']
        lat = request.form['lat']
        logger.info('This is an INFO message')
        logger.info(body)

        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, lng = ?, lat = ?'
                ' WHERE id = ?',
                (title, body, lng, lat, id)
            )
            db.commit()
            return redirect(url_for('blog.blog'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.blog'))


# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def upload_file():
#     logger.info("img dir:")
#     logger.info(current_app.config['UPLOAD_FOLDER'])

#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # if user does not select file, browser also
#         # submit a empty part without filename
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             logger.info(current_app.config['UPLOAD_FOLDER'])
#             file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('download_file', name=filename))



# @bp.route('/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('download_file', name=filename))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''