import secrets
from datetime import datetime
from coeno import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Company(db.Model):
    id = db.Column(db.String(4), primary_key=True, default=secrets.token_hex(2))
    name = db.Column(db.String(120), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default_company.jpg')
    users = db.relationship('User', backref='company', lazy=True, cascade='all,delete')
    posts = db.relationship('Post', backref='company', lazy=True, cascade='all,delete')
    decisions = db.relationship('Decision', backref='company', lazy=True, cascade='all,delete')
    feedbacks = db.relationship('Feedback', backref='company', lazy=True, cascade='all,delete')
    polls = db.relationship('Poll', backref='company', lazy=True, cascade='all,delete')
    departments = db.relationship('Department', backref='company', lazy=True, cascade='all,delete')
    topics = db.relationship('Topic', backref='company', lazy=True, cascade='all,delete')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(120), nullable=False) #owner, admin, or member
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all,delete')
    decisions = db.relationship('Decision', backref='author', lazy=True, cascade='all,delete')
    steps = db.relationship('Step', backref='author', lazy=True, cascade='all,delete')
    feedbacks = db.relationship('Feedback', backref='author', lazy=True, cascade='all,delete')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all,delete')
    poll_items = db.relationship('PollItem', backref='author', lazy=True, cascade='all,delete')
    polls = db.relationship('Poll', backref='author', lazy=True, cascade='all,delete')
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)
    liked = db.relationship('PostLike', foreign_keys='PostLike.user_id', backref='user', lazy='dynamic', cascade='all,delete')
    disliked = db.relationship('PostDisLike', foreign_keys='PostDisLike.user_id', backref='user', lazy='dynamic', cascade='all,delete')
    voted = db.relationship('ItemVote', foreign_keys='ItemVote.user_id', backref='user', lazy='dynamic', cascade='all,delete')

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.id,
            PostLike.post_id == post.id).count() > 0

    def dislike_post(self, post):
        if not self.has_disliked_post(post):
            dislike = PostDisLike(user_id=self.id, post_id=post.id)
            db.session.add(dislike)

    def undislike_post(self, post):
        if self.has_disliked_post(post):
            PostDisLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_disliked_post(self, post):
        return PostDisLike.query.filter(
            PostDisLike.user_id == self.id,
            PostDisLike.post_id == post.id).count() > 0

    def vote(self, poll_item):
        if not self.has_voted(poll_item):
            vote = ItemVote(user_id=self.id, poll_item_id=poll_item.id)
            db.session.add(vote)

    def unvote(self, poll_item):
        if self.has_voted(poll_item):
            ItemVote.query.filter_by(
                user_id=self.id,
                poll_item_id=poll_item.id).delete()

    def has_voted(self, poll_item):
        return ItemVote.query.filter(
            ItemVote.user_id == self.id,
            ItemVote.poll_item_id == poll_item.id).count() > 0

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class PostDisLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    view_count = db.Column(db.Integer, nullable=True, default=0)
    type = db.Column(db.String(100), nullable=False) # notion, suggestion, response
    department = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all,delete')
    dislikes = db.relationship('PostDisLike', backref='post', lazy='dynamic', cascade='all,delete')
    responses = db.relationship('Post', lazy=True, cascade='all,delete')
Post.original_post_id = db.Column(db.Integer, db.ForeignKey(Post.id))


class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    department = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    steps = db.relationship('Step', backref='decision', lazy=True, cascade='all,delete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    complete = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    department = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    comments = db.relationship('Comment', backref='feedback', lazy=True, cascade='all,delete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(100), nullable=False) # support, agree, recognize, disagree
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=False)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    department = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    poll_items = db.relationship('PollItem', backref='poll', lazy=True, cascade='all,delete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)

class PollItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.String(4), db.ForeignKey('poll.id'), nullable=False)
    votes = db.relationship('ItemVote', backref='poll_item', lazy='dynamic', cascade='all,delete')

class ItemVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    poll_item_id = db.Column(db.Integer, db.ForeignKey('poll_item.id'))

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.String(4), db.ForeignKey('company.id'), nullable=False)
