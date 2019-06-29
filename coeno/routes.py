import os
import secrets
from PIL import Image
from sqlalchemy import desc
from flask import render_template, url_for, flash, redirect, request, abort
from coeno import app, db, bcrypt
from coeno.forms import MemberRegistrationForm, CompanyRegistrationForm, LoginForm, UpdateAccountForm, PostForm
from coeno.models import User, Post, Company
from flask_login import login_user, current_user, logout_user, login_required


@app.route('/')
@app.route("/home")
@login_required
def home():
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    posts = Post.query.all()
    top_post = Post.query.order_by(desc(Post.view_count)).first()

    return render_template("index.html", posts=posts, image_file=image_file, top_post=top_post)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/register/company", methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        company = Company(name=form.company_name.data)
        db.session.add(company)
        db.session.commit()
        user = User(username=form.username.data, first_name=form.first_name.data, last_name=form.last_name.data, role="owner", email=form.email.data, company_id=company.id, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your workspace has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register_company.html', form=form)

@app.route("/register/<string:company_id>", methods=['GET', 'POST'])
def register_member(company_id):
    form = MemberRegistrationForm()
    company = Company.query.get_or_404(company_id)
    company_name = company.name

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, first_name=form.first_name.data, last_name=form.last_name.data, role="member", email=form.email.data, company_id=company_id, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register_member.html', form=form, company_name=company_name)

@app.route("/login/<string:company_id>", methods=['GET', 'POST'])
def login(company_id):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    company = Company.query.get_or_404(company_id)
    company_name = company.name

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html', form=form, company_name=company_name)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post', image_file=image_file)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if post.author != current_user:
        post.view_count += 1
        db.session.commit()

    return render_template('post.html', title=post.title, post=post, image_file=image_file)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))
