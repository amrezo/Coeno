import os
import secrets
from PIL import Image
from sqlalchemy import desc
from flask import render_template, url_for, flash, redirect, request, abort
from coeno import app, db, bcrypt
from coeno.forms import MemberRegistrationForm, CompanyRegistrationForm, LoginForm, UpdateAccountForm, PostForm, ResponseForm, FindLogin, UpdateCompanyForm, DecisionForm, StepForm, FeedbackForm, CommentForm, PollForm, PollItemForm
from coeno.models import User, Post, Company, Department, Topic, Decision, Step, Feedback, Comment, Poll, PollItem
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
def landing():
    if current_user.is_authenticated:
        company_id = current_user.company_id
        return redirect(url_for('home', company_id=company_id))
    else:
        return render_template("landing.html")

@app.route("/home/<string:company_id>")
def home(company_id):
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        posts = Post.query.filter_by(company_id=company_id).order_by(desc(Post.date_posted)).limit(8).all()
        decisions = Decision.query.filter_by(company_id=company_id).order_by(desc(Decision.date_posted)).limit(8).all()
        feedbacks = Feedback.query.filter_by(company_id=company_id).order_by(desc(Feedback.date_posted)).limit(8).all()
        polls = Poll.query.filter_by(company_id=company_id).order_by(desc(Poll.date_posted)).limit(8).all()
        top_posts = Post.query.filter_by(company_id=company_id).order_by(desc(Post.view_count)).limit(4).all()

        depts = Department.query.filter_by(company_id=company_id).all()

        return render_template("index.html", posts=posts, decisions=decisions, feedbacks=feedbacks, polls=polls, image_file=image_file, top_posts=top_posts, company_id=company_id, depts=depts)
    else:
        flash('Please login to your company workspace to continue.', 'info')
        return redirect(url_for('login', company_id=company_id))

@app.route("/register/company", methods=['GET', 'POST'])
def register_company():
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        company = Company(name=form.company_name.data, id=secrets.token_hex(2))
        db.session.add(company)
        db.session.commit()
        user = User(username=form.username.data, first_name=form.first_name.data, last_name=form.last_name.data, role="owner", email=form.email.data, company_id=company.id, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your company workspace has been created! You are now able to log in', 'success')
        return redirect(url_for('login', company_id=company.id))
    return render_template('register_company.html', form=form)

@app.route("/register/member/<string:company_id>", methods=['GET', 'POST'])
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
        return redirect(url_for('login', company_id=company_id))
    return render_template('register_member.html', form=form, company_name=company_name)

@app.route("/login/<string:company_id>", methods=['GET', 'POST'])
def login(company_id):
    if current_user.is_authenticated:
        return redirect(url_for('home', company_id=company_id))
    form = LoginForm()
    company = Company.query.get_or_404(company_id)
    company_name = company.name

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home', company_id=company_id))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('signin.html', form=form, company_name=company_name)

@app.route("/<string:company_id>/logout")
def logout(company_id):
    logout_user()
    return redirect(url_for('login', company_id=company_id))

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

@app.route("/<string:company_id>/account", methods=['GET', 'POST'])
@login_required
def account(company_id):
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.title = form.title.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account', company_id=company_id))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.title.data = current_user.title
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', image_file=image_file, form=form, company_id=company_id)

@app.route("/<string:company_id>/company", methods=['GET', 'POST'])
@login_required
def company(company_id):
    form = UpdateCompanyForm()
    company = Company.query.get_or_404(company_id)
    company_image = url_for('static', filename='profile_pics/' + company.image_file)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            company.image_file = picture_file
        company.name = form.name.data
        departments = Department.query.filter_by(company_id=company.id).all()
        for dept in departments:
            db.session.delete(dept)
        depts_string = form.departments.data
        depts_list = depts_string.split(",")
        for dept in depts_list:
            dept = Department(title=dept, company_id=company.id)
            db.session.add(dept)
        db.session.commit()
        flash('Your company profile has been updated!', 'success')
        return redirect(url_for('company', company_id=company_id))
    elif request.method == 'GET':
        form.name.data = company.name
        departments = Department.query.filter_by(company_id=company.id).all()
        depts_list = []
        for dept in departments:
            dept_title = dept.title
            depts_list.append(dept_title)
        depts_string = ','.join(depts_list)
        form.departments.data = depts_string

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('company.html', image_file=image_file, form=form, company_id=company_id, company=company, company_image=company_image)

@app.route("/<string:company_id>/post/new", methods=['GET', 'POST'])
@login_required
def new_post(company_id):
    depts = Department.query.filter_by(company_id=company_id).all()
    depts_list = [(i.id, i.title) for i in depts]

    form = PostForm()
    form.department.choices = depts_list

    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        post_topic = Topic(title=form.topic.data, company_id=company_id)
        db.session.add(post_topic)
        db.session.commit()
        post = Post(title=form.title.data, content=form.content.data, author=current_user, type=form.type.data, department=form.department.data, topic=form.topic.data, company_id=company_id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home', company_id=company_id))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/decision/new", methods=['GET', 'POST'])
@login_required
def new_decision(company_id):
    depts = Department.query.filter_by(company_id=company_id).all()
    depts_list = [(i.id, i.title) for i in depts]

    form = DecisionForm()
    form.department.choices = depts_list

    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        decision_topic = Topic(title=form.topic.data, company_id=company_id)
        db.session.add(decision_topic)
        db.session.commit()
        decision = Decision(title=form.title.data, author=current_user, department=form.department.data, topic=form.topic.data, company_id=company_id)
        db.session.add(decision)
        db.session.commit()
        flash('Your decision has been created! You can now add steps to it.', 'success')
        return redirect(url_for('decision', company_id=company_id, decision_id=decision.id))
    return render_template('create_decision.html', title='New Decision', form=form, legend='New Decision', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/<int:decision_id>/step/new", methods=['GET', 'POST'])
@login_required
def new_step(decision_id, company_id):
    form = StepForm()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        step = Step(title=form.title.data, content=form.content.data, number=form.number.data, decision_id=decision_id, author=current_user)
        db.session.add(step)
        db.session.commit()
        flash('Your step has been created!', 'success')
        return redirect(url_for('decision', company_id=company_id, decision_id=decision_id))
    return render_template('create_step.html', title='New Step', form=form, legend='New Step', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/<int:poll_id>/item/new", methods=['GET', 'POST'])
@login_required
def new_poll_item(poll_id, company_id):
    form = PollItemForm()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        item = PollItem(title=form.title.data, poll_id=poll_id, author=current_user)
        db.session.add(item)
        db.session.commit()
        flash('Your poll item has been created!', 'success')
        return redirect(url_for('poll', company_id=company_id, poll_id=poll_id))
    return render_template('create_item.html', title='New Poll Item', form=form, legend='New Poll Item', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/<int:feedback_id>/comment/new", methods=['GET', 'POST'])
@login_required
def new_comment(feedback_id, company_id):
    form = CommentForm()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        comment = Comment(title=form.title.data, content=form.content.data, type=form.type.data, feedback_id=feedback_id, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been created!', 'success')
        return redirect(url_for('feedback', company_id=company_id, feedback_id=feedback_id))
    return render_template('create_comment.html', title='New Comment', form=form, legend='New Comment', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/poll/new", methods=['GET', 'POST'])
@login_required
def new_poll(company_id):
    depts = Department.query.filter_by(company_id=company_id).all()
    depts_list = [(i.id, i.title) for i in depts]

    form = PollForm()
    form.department.choices = depts_list

    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        poll_topic = Topic(title=form.topic.data, company_id=company_id)
        db.session.add(poll_topic)
        db.session.commit()
        poll = Poll(title=form.title.data, author=current_user, department=form.department.data, topic=form.topic.data, company_id=company_id)
        db.session.add(poll)
        db.session.commit()
        flash('Your poll has been created! You can now add items to it.', 'success')
        return redirect(url_for('poll', company_id=company_id, poll_id=poll.id))
    return render_template('create_poll.html', title='New Poll', form=form, legend='New Poll', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/feedback/new", methods=['GET', 'POST'])
@login_required
def new_feedback(company_id):
    depts = Department.query.filter_by(company_id=company_id).all()
    depts_list = [(i.id, i.title) for i in depts]

    form = FeedbackForm()
    form.department.choices = depts_list

    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        feedback_topic = Topic(title=form.topic.data, company_id=company_id)
        db.session.add(feedback_topic)
        db.session.commit()
        feedback = Feedback(title=form.title.data, content=form.content.data, author=current_user, department=form.department.data, topic=form.topic.data, company_id=company_id)
        db.session.add(feedback)
        db.session.commit()
        flash('Your feedback request has been created!', 'success')
        return redirect(url_for('feedback', company_id=company_id, feedback_id=feedback.id))
    return render_template('create_feedback.html', title='New Feedback Request', form=form, legend='New Feedback Request', image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/response/<int:post_id>", methods=['GET', 'POST'])
@login_required
def response(company_id, post_id):
    original_post = Post.query.get_or_404(post_id)
    form = ResponseForm()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if form.validate_on_submit():
        response = Post(title=form.title.data, content=form.content.data, author=current_user, type='response', company_id=company_id, department=original_post.department, topic=original_post.topic)
        original_post.responses.append(response)
        db.session.add(response)
        db.session.commit()
        flash('Your response has been created!', 'success')
        return redirect(url_for('post', company_id=company_id, post_id=response.id))
    return render_template('create_response.html', title='New Response', form=form, legend='New Response', image_file=image_file, company_id=company_id)


@app.route("/<string:company_id>/post/<int:post_id>")
def post(post_id, company_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    if post.author != current_user:
        post.view_count += 1
        db.session.commit()

    return render_template('post.html', title=post.title, post=post, image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/decision/<int:decision_id>")
def decision(decision_id, company_id):
    decision = Decision.query.get_or_404(decision_id)
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    return render_template('decision.html', title=decision.title, decision=decision, image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/poll/<int:poll_id>")
def poll(poll_id, company_id):
    poll = Poll.query.get_or_404(poll_id)
    vote = current_user.voted.filter_by(id=poll_id).first()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    return render_template('poll.html', title=poll.title, poll=poll, image_file=image_file, company_id=company_id, vote=vote)

@app.route("/<string:company_id>/feedback/<int:feedback_id>")
def feedback(feedback_id, company_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        image_file = ''
    return render_template('feedback.html', title=feedback.title, feedback=feedback, image_file=image_file, company_id=company_id)

@app.route("/<string:company_id>/decision/<int:decision_id>/delete", methods=['POST'])
@login_required
def delete_decision(decision_id, company_id):
    decision = Decision.query.get_or_404(decision_id)
    if decision.author != current_user:
        abort(403)
    db.session.delete(decision)
    db.session.commit()
    flash('Your decision has been deleted!', 'success')
    return redirect(url_for('home', company_id=company_id))

@app.route("/<string:company_id>/poll/<int:poll_id>/delete", methods=['POST'])
@login_required
def delete_poll(poll_id, company_id):
    poll = Poll.query.get_or_404(poll_id)
    if poll.author != current_user:
        abort(403)
    db.session.delete(poll)
    db.session.commit()
    flash('Your poll has been deleted!', 'success')
    return redirect(url_for('home', company_id=company_id))

@app.route("/<string:company_id>/feedback/<int:feedback_id>/delete", methods=['POST'])
@login_required
def delete_feedback(feedback_id, company_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.author != current_user:
        abort(403)
    db.session.delete(feedback)
    db.session.commit()
    flash('Your feedback request has been deleted!', 'success')
    return redirect(url_for('home', company_id=company_id))

@app.route('/like/<int:post_id>/<action>')
def like_action(post_id, action):
    post = Post.query.get_or_404(post_id)
    if action == 'like':
        current_user.like_post(post)
        current_user.undislike_post(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/dislike/<int:post_id>/<action>')
def dislike_action(post_id, action):
    post = Post.query.get_or_404(post_id)
    if action == 'dislike':
        current_user.dislike_post(post)
        current_user.unlike_post(post)
        db.session.commit()
    if action == 'undislike':
        current_user.undislike_post(post)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/vote/<int:poll_item_id>/<action>')
def vote(poll_item_id, action):
    poll_item = PollItem.query.get_or_404(poll_item_id)
    if action == 'vote':
        current_user.vote(poll_item)
        db.session.commit()
    if action == 'unvote':
        current_user.unvote(poll_item)
        db.session.commit()
    return redirect(request.referrer)

@app.route("/<string:company_id>/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id, company_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.type = form.type.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id, company_id=company_id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form_content = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post', company_id=company_id, form_content=form_content)


@app.route("/<string:company_id>/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id, company_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home', company_id=company_id))

@app.route("/<string:company_id>/step/<int:step_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_step(step_id, company_id):
    step = Step.query.get_or_404(step_id)
    if step.author != current_user:
        abort(403)
    db.session.delete(step)
    db.session.commit()
    flash('Your step has been deleted!', 'success')
    return redirect(request.referrer)

@app.route("/<string:company_id>/comment/<int:comment_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_comment(comment_id, company_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(request.referrer)

@app.route("/<string:company_id>/item/<int:item_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_item(item_id, company_id):
    item = PollItem.query.get_or_404(item_id)
    if item.author != current_user:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Your poll item has been deleted!', 'success')
    return redirect(request.referrer)

@app.route("/<string:company_id>/step/<int:step_id>/done", methods=['POST', 'GET'])
@login_required
def mark_step_done(step_id, company_id):
    step = Step.query.get_or_404(step_id)
    step.complete = True
    db.session.commit()
    flash('Your step was marked as done!', 'success')
    return redirect(request.referrer)

@app.route("/<string:company_id>/step/<int:step_id>/undone", methods=['POST', 'GET'])
@login_required
def mark_step_undone(step_id, company_id):
    step = Step.query.get_or_404(step_id)
    step.complete = False
    db.session.commit()
    flash('Your step was marked as not done!', 'success')
    return redirect(request.referrer)

@app.route("/login", methods=['GET','POST'])
def find_login():
    if current_user.is_authenticated:
        company_id = current_user.company_id
        return redirect(url_for('home', company_id=company_id))
    else:
        form = FindLogin()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                company_id = user.company_id
                return redirect(url_for('login', company_id=company_id))
            else:
                flash('No account with this email found. Please check your email and try again.', 'danger')
        return render_template('findlogin.html', form=form)
