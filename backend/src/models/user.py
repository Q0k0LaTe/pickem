from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    steam_id = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.Text)
    profile_url = db.Column(db.Text)
    real_name = db.Column(db.String(200))
    country_code = db.Column(db.String(2))
    viewer_pass_tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    picks = db.relationship('Pick', backref='user', lazy=True, cascade='all, delete-orphan')
    optimization_jobs = db.relationship('OptimizationJob', backref='user', lazy=True, cascade='all, delete-orphan')
    templates = db.relationship('Template', backref='author', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'steam_id': self.steam_id,
            'username': self.username,
            'avatar_url': self.avatar_url,
            'profile_url': self.profile_url,
            'real_name': self.real_name,
            'country_code': self.country_code,
            'viewer_pass_tokens': self.viewer_pass_tokens,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'is_active': self.is_active
        }

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = db.Column(db.String(50), unique=True, nullable=False)
    team_a = db.Column(db.String(100), nullable=False)
    team_b = db.Column(db.String(100), nullable=False)
    team_a_logo_url = db.Column(db.Text)
    team_b_logo_url = db.Column(db.Text)
    stage = db.Column(db.String(20), nullable=False)  # 'swiss' or 'playoffs'
    round_number = db.Column(db.Integer, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='upcoming')  # 'upcoming', 'live', 'completed', 'cancelled'
    result = db.Column(db.String(10))  # 'team_a', 'team_b', 'draw'
    is_safe = db.Column(db.Boolean, default=False)
    confidence_threshold = db.Column(db.Float, default=0.75)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    odds = db.relationship('Odds', backref='match', lazy=True, cascade='all, delete-orphan')
    picks = db.relationship('Pick', backref='match', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='match', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Match {self.team_a} vs {self.team_b}>'

    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'team_a': self.team_a,
            'team_b': self.team_b,
            'team_a_logo_url': self.team_a_logo_url,
            'team_b_logo_url': self.team_b_logo_url,
            'stage': self.stage,
            'round_number': self.round_number,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'status': self.status,
            'result': self.result,
            'is_safe': self.is_safe,
            'confidence_threshold': self.confidence_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Odds(db.Model):
    __tablename__ = 'odds'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('matches.id'), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    team_a_win_prob = db.Column(db.Float, nullable=False)
    team_b_win_prob = db.Column(db.Float, nullable=False)
    raw_data = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    @property
    def implied_win_rate(self):
        return max(self.team_a_win_prob, self.team_b_win_prob)

    def __repr__(self):
        return f'<Odds {self.source} for match {self.match_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'source': self.source,
            'team_a_win_prob': self.team_a_win_prob,
            'team_b_win_prob': self.team_b_win_prob,
            'implied_win_rate': self.implied_win_rate,
            'raw_data': self.raw_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_active': self.is_active
        }

class Pick(db.Model):
    __tablename__ = 'picks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    match_id = db.Column(db.String(36), db.ForeignKey('matches.id'), nullable=False)
    selected_team = db.Column(db.String(10), nullable=False)  # 'team_a' or 'team_b'
    confidence = db.Column(db.Float, default=0.5)
    is_locked = db.Column(db.Boolean, default=False)
    pick_type = db.Column(db.String(20), default='manual')  # 'manual', 'optimized', 'template'
    template_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'match_id', name='unique_user_match_pick'),)

    def __repr__(self):
        return f'<Pick {self.selected_team} for match {self.match_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'match_id': self.match_id,
            'selected_team': self.selected_team,
            'confidence': self.confidence,
            'is_locked': self.is_locked,
            'pick_type': self.pick_type,
            'template_id': self.template_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OptimizationJob(db.Model):
    __tablename__ = 'optimization_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    safe_picks = db.Column(db.JSON, default=list)
    unsafe_picks = db.Column(db.JSON, default=list)
    constraints = db.Column(db.JSON, default=dict)
    result = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    execution_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<OptimizationJob {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'safe_picks': self.safe_picks,
            'unsafe_picks': self.unsafe_picks,
            'constraints': self.constraints,
            'result': self.result,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Template(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    picks = db.Column(db.JSON, default=list)
    performance_stats = db.Column(db.JSON, default=dict)
    is_public = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Template {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'author_id': self.author_id,
            'picks': self.picks,
            'performance_stats': self.performance_stats,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'usage_count': self.usage_count,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    match_id = db.Column(db.String(36), db.ForeignKey('matches.id'), nullable=False)
    predicted_team = db.Column(db.String(10), nullable=False)
    actual_result = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'match_id', name='unique_user_match_result'),)

    def __repr__(self):
        return f'<Result {self.predicted_team} for match {self.match_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'match_id': self.match_id,
            'predicted_team': self.predicted_team,
            'actual_result': self.actual_result,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

