from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# Global db instance
_db = SQLAlchemy()

def get_db():
    return _db   # <-- must be indented

class User(_db.Model):
    __tablename__ = "users"
    id = _db.Column(_db.String(64), primary_key=True)  # session-based UUID
    email = _db.Column(_db.String(255), unique=True, nullable=True)
    is_pro = _db.Column(_db.Boolean, default=False)
    pro_until = _db.Column(_db.DateTime, nullable=True)
    created_at = _db.Column(_db.DateTime, default=datetime.utcnow)

    def activate_pro(self, duration_days: int = 365):
        now = datetime.utcnow()
        if self.pro_until and self.pro_until > now:
            self.pro_until += timedelta(days=duration_days)
        else:
            self.pro_until = now + timedelta(days=duration_days)
        self.is_pro = True

class Entry(_db.Model):
    __tablename__ = "entries"
    id = _db.Column(_db.Integer, primary_key=True, autoincrement=True)
    user_id = _db.Column(_db.String(64), _db.ForeignKey("users.id"), index=True)
    text = _db.Column(_db.Text, nullable=False)
    top_emotion = _db.Column(_db.String(64))
    top_score = _db.Column(_db.Float)
    scores_json = _db.Column(_db.Text)  # serialized dict of label->score
    created_at = _db.Column(_db.DateTime, default=datetime.utcnow, index=True)

class Payment(_db.Model):
    __tablename__ = "payments"
    id = _db.Column(_db.Integer, primary_key=True, autoincrement=True)
    user_id = _db.Column(_db.String(64), index=True)
    tx_ref = _db.Column(_db.String(128), unique=True, index=True)
    flw_tx_id = _db.Column(_db.String(64), unique=True, nullable=True)
    status = _db.Column(_db.String(64), default="initialized")  # initialized | successful | failed
    amount = _db.Column(_db.Float)
    currency = _db.Column(_db.String(16))
    raw_json = _db.Column(_db.Text)
    created_at = _db.Column(_db.DateTime, default=datetime.utcnow)
