from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo
from enum import Enum

class ChallengeCategory(Enum):
    WEB = "web"
    CRYPTO = "crypto"
    FORENSICS = "forensics"
    REVERSE = "reverse"
    PWNABLE = "pwnable"
    MISC = "misc"

class ChallengeDifficulty(Enum):
    EASY = "kolay"
    MEDIUM = "orta"
    HARD = "zor"
    EXPERT = "uzman"

class Challenge:
    def __init__(self, title=None, description=None, category=None, difficulty=None,
                 points=None, flag=None, hints=None, files=None, is_active=True,
                 created_by=None, _id=None):
        self.title = title
        self.description = description
        self.category = category
        self.difficulty = difficulty
        self.points = points or 0
        self.flag = flag
        self.hints = hints or []
        self.files = files or []
        self.is_active = is_active
        self.created_by = created_by
        self._id = _id
        self.created_at = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, challenge_id):
        challenge_data = mongo.db.challenges.find_one({"_id": ObjectId(challenge_id)})
        if challenge_data:
            return cls.from_dict(challenge_data)
        return None
    
    @classmethod
    def get_all(cls, only_active=False, category=None):
        query = {}
        if only_active:
            query["is_active"] = True
        if category:
            query["category"] = category
            
        cursor = mongo.db.challenges.find(query).sort("points", 1)
        return [cls.from_dict(challenge_data) for challenge_data in cursor]
    
    @classmethod
    def from_dict(cls, data):
        challenge = cls()
        challenge.title = data.get('title')
        challenge.description = data.get('description')
        challenge.category = data.get('category')
        challenge.difficulty = data.get('difficulty')
        challenge.points = data.get('points', 0)
        challenge.flag = data.get('flag')
        challenge.hints = data.get('hints', [])
        challenge.files = data.get('files', [])
        challenge.is_active = data.get('is_active', True)
        challenge.created_by = data.get('created_by')
        challenge.created_at = data.get('created_at', datetime.utcnow())
        challenge._id = data.get('_id')
        return challenge
    
    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "points": self.points,
            "flag": self.flag,
            "hints": self.hints,
            "files": self.files,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at
        }
    
    def save(self):
        if self._id:
            # Update existing challenge
            mongo.db.challenges.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new challenge
            challenge_dict = self.to_dict()
            result = mongo.db.challenges.insert_one(challenge_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.challenges.delete_one({"_id": ObjectId(self._id)})
            # Ayrıca ilgili sübmisyonları da siliyoruz
            mongo.db.submissions.delete_many({"challenge_id": str(self._id)})
            return True
        return False
    
    @property
    def solved_count(self):
        """Bu görevi çözen kullanıcı sayısını döndürür"""
        return mongo.db.submissions.count_documents({
            "challenge_id": str(self._id),
            "is_correct": True
        })
    
    @classmethod
    def get_solved_by_user(cls, user_id):
        """Bir kullanıcının çözdüğü tüm görevleri döndürür"""
        # Kullanıcının doğru çözdüğü görevlerin ID'lerini al
        correct_submissions = mongo.db.submissions.find({
            "user_id": user_id,
            "is_correct": True
        })
        challenge_ids = [sub["challenge_id"] for sub in correct_submissions]
        
        # Bu ID'lere sahip görevleri al
        solved_challenges = []
        for challenge_id in challenge_ids:
            challenge = cls.get_by_id(challenge_id)
            if challenge:
                solved_challenges.append(challenge)
        
        return solved_challenges

class Submission:
    def __init__(self, user_id=None, challenge_id=None, flag_submitted=None,
                 is_correct=False, points=0, _id=None):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.flag_submitted = flag_submitted
        self.is_correct = is_correct
        self.points = points
        self._id = _id
        self.submitted_at = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, submission_id):
        submission_data = mongo.db.submissions.find_one({"_id": ObjectId(submission_id)})
        if submission_data:
            return cls.from_dict(submission_data)
        return None
    
    @classmethod
    def get_by_user_and_challenge(cls, user_id, challenge_id):
        submission_data = mongo.db.submissions.find_one({
            "user_id": user_id,
            "challenge_id": challenge_id,
            "is_correct": True
        })
        if submission_data:
            return cls.from_dict(submission_data)
        return None
    
    @classmethod
    def get_by_user(cls, user_id):
        cursor = mongo.db.submissions.find({"user_id": user_id})
        return [cls.from_dict(submission_data) for submission_data in cursor]
    
    @classmethod
    def get_correct_submissions_by_user(cls, user_id):
        cursor = mongo.db.submissions.find({
            "user_id": user_id,
            "is_correct": True
        })
        return [cls.from_dict(submission_data) for submission_data in cursor]
    
    @classmethod
    def from_dict(cls, data):
        submission = cls()
        submission.user_id = data.get('user_id')
        submission.challenge_id = data.get('challenge_id')
        submission.flag_submitted = data.get('flag_submitted')
        submission.is_correct = data.get('is_correct', False)
        submission.points = data.get('points', 0)
        submission.submitted_at = data.get('submitted_at', datetime.utcnow())
        submission._id = data.get('_id')
        return submission
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "challenge_id": self.challenge_id,
            "flag_submitted": self.flag_submitted,
            "is_correct": self.is_correct,
            "points": self.points,
            "submitted_at": self.submitted_at
        }
    
    def save(self):
        # Submit tarihi belirtilmemişse şu anki tarihi kullan
        if not hasattr(self, 'submitted_at') or self.submitted_at is None:
            self.submitted_at = datetime.utcnow()
        
        if self._id:
            # Update existing submission
            mongo.db.submissions.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new submission
            submission_dict = self.to_dict()
            result = mongo.db.submissions.insert_one(submission_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.submissions.delete_one({"_id": ObjectId(self._id)})
            return True
        return False

class Badge:
    def __init__(self, name=None, description=None, image_url=None, criteria=None,
                 created_by=None, _id=None):
        self.name = name
        self.description = description
        self.image_url = image_url
        self.criteria = criteria or {} # Örn: {"min_points": 100, "category": "web"}
        self.created_by = created_by
        self._id = _id
        self.created_at = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, badge_id):
        badge_data = mongo.db.badges.find_one({"_id": ObjectId(badge_id)})
        if badge_data:
            return cls.from_dict(badge_data)
        return None
    
    @classmethod
    def get_all(cls):
        cursor = mongo.db.badges.find()
        return [cls.from_dict(badge_data) for badge_data in cursor]
    
    @classmethod
    def from_dict(cls, data):
        badge = cls()
        badge.name = data.get('name')
        badge.description = data.get('description')
        badge.image_url = data.get('image_url')
        badge.criteria = data.get('criteria', {})
        badge.created_by = data.get('created_by')
        badge.created_at = data.get('created_at', datetime.utcnow())
        badge._id = data.get('_id')
        return badge
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "criteria": self.criteria,
            "created_by": self.created_by,
            "created_at": self.created_at
        }
    
    def save(self):
        if self._id:
            # Update existing badge
            mongo.db.badges.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new badge
            badge_dict = self.to_dict()
            result = mongo.db.badges.insert_one(badge_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.badges.delete_one({"_id": ObjectId(self._id)})
            return True
        return False

class UserBadge:
    def __init__(self, user_id=None, badge_id=None, _id=None):
        self.user_id = user_id
        self.badge_id = badge_id
        self._id = _id
        self.awarded_at = datetime.utcnow()
        
    @classmethod
    def get_by_user(cls, user_id):
        cursor = mongo.db.user_badges.find({"user_id": user_id})
        return [cls.from_dict(user_badge_data) for user_badge_data in cursor]
    
    @classmethod
    def get_by_user_and_badge(cls, user_id, badge_id):
        user_badge_data = mongo.db.user_badges.find_one({
            "user_id": user_id,
            "badge_id": badge_id
        })
        if user_badge_data:
            return cls.from_dict(user_badge_data)
        return None
    
    @classmethod
    def from_dict(cls, data):
        user_badge = cls()
        user_badge.user_id = data.get('user_id')
        user_badge.badge_id = data.get('badge_id')
        user_badge.awarded_at = data.get('awarded_at', datetime.utcnow())
        user_badge._id = data.get('_id')
        return user_badge
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "badge_id": self.badge_id,
            "awarded_at": self.awarded_at
        }
    
    def save(self):
        if self._id:
            # Update existing user badge
            mongo.db.user_badges.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new user badge
            user_badge_dict = self.to_dict()
            result = mongo.db.user_badges.insert_one(user_badge_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.user_badges.delete_one({"_id": ObjectId(self._id)})
            return True
        return False 