from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class UserRole:
    USER = "user"
    MEMBER = "member"
    ADMIN = "admin"

class User(UserMixin):
    def __init__(self, username=None, email=None, password=None, role=UserRole.USER, _id=None, created_at=None):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.role = role
        self._id = _id
        self.created_at = created_at or datetime.utcnow()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self._id)
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_member(self):
        return self.role == UserRole.MEMBER or self.role == UserRole.ADMIN
    
    @classmethod
    def get_by_id(cls, user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def get_by_email(cls, email):
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def get_by_username(cls, username):
        user_data = mongo.db.users.find_one({"username": username})
        if user_data:
            return cls.from_dict(user_data)
        return None
    
    @classmethod
    def from_dict(cls, data):
        user = cls()
        user.username = data.get('username')
        user.email = data.get('email')
        user.password_hash = data.get('password_hash')
        user.role = data.get('role', UserRole.USER)
        user._id = data.get('_id')
        user.created_at = data.get('created_at', datetime.utcnow())
        return user
    
    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "created_at": self.created_at
        }
    
    def save(self):
        if self._id:
            # Update existing user
            mongo.db.users.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "username": self.username,
                    "email": self.email,
                    "password_hash": self.password_hash,
                    "role": self.role
                }}
            )
        else:
            # Insert new user
            user_dict = self.to_dict()
            result = mongo.db.users.insert_one(user_dict)
            self._id = result.inserted_id
        return self 