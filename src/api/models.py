from src.api.db import db


def create_db_tables():
    db.create_all()


class User(db.Model):
    # Subject ID
    sub = db.Column(db.String(64), primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)

    jtis = db.relationship("JTI")
    access_tokens = db.relationship("AccessToken")

    def __repr__(self):
        return f"<User {self.sub}:{self.email}>"


class JTI(db.Model):
    # JWT Token ID
    jti = db.Column(db.String(128), primary_key=True)

    # Expiration
    exp = db.Column(db.Integer)

    # Issued at Time
    iat = db.Column(db.Integer)

    user = db.Column(db.String(64), db.ForeignKey("user.sub"))

    def __repr__(self):
        return f"<Token {self.jti} - User: {self.user}>"


class AccessToken(db.Model):
    token_id = db.Column(db.String(256), primary_key=True)
    user = db.Column(db.String(64), db.ForeignKey("user.sub"))
    exp = db.Column(db.Integer)

    def __repr__(self):
        return f"<AccessToken{self.user} {self.token_id[:16]}... >"
