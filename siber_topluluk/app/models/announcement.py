from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class Announcement:
    def __init__(self, title=None, content=None, created_at=None, _id=None, 
                 updated_at=None, author_id=None, image_url=None, is_active=True):
        self.title = title
        self.content = content
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self._id = _id
        self.author_id = author_id
        self.image_url = image_url
        self.is_active = is_active
    
    @classmethod
    def get_by_id(cls, announcement_id):
        announcement_data = mongo.db.announcements.find_one({"_id": ObjectId(announcement_id)})
        if announcement_data:
            return cls.from_dict(announcement_data)
        return None
    
    @classmethod
    def get_all(cls, limit=None, skip=0, active_only=True):
        query = {}
        if active_only:
            query["is_active"] = True
        
        announcements_data = mongo.db.announcements.find(query).sort("created_at", -1).skip(skip)
        if limit:
            announcements_data = announcements_data.limit(limit)
        
        return [cls.from_dict(announcement) for announcement in announcements_data]
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data.get('title'),
            content=data.get('content'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=data.get('_id'),
            author_id=data.get('author_id'),
            image_url=data.get('image_url'),
            is_active=data.get('is_active', True)
        )
    
    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author_id": self.author_id,
            "image_url": self.image_url,
            "is_active": self.is_active
        }
    
    def save(self):
        now = datetime.utcnow()
        self.updated_at = now
        
        if self._id:
            # Update existing announcement
            mongo.db.announcements.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "title": self.title,
                    "content": self.content,
                    "updated_at": now,
                    "author_id": self.author_id,
                    "image_url": self.image_url,
                    "is_active": self.is_active
                }}
            )
        else:
            # Insert new announcement
            self.created_at = now
            announcement_dict = self.to_dict()
            result = mongo.db.announcements.insert_one(announcement_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.announcements.delete_one({"_id": ObjectId(self._id)})
            return True
        return False
    
    def deactivate(self):
        if self._id:
            self.is_active = False
            mongo.db.announcements.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {"is_active": False}}
            )
            return True
        return False 