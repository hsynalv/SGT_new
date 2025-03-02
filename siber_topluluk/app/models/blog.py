from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class Blog:
    def __init__(self, title=None, content=None, author_id=None, created_at=None, _id=None, 
                 updated_at=None, tags=None, image_url=None, likes=None, views=0):
        self.title = title
        self.content = content
        self.author_id = author_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self._id = _id
        self.tags = tags or []
        self.image_url = image_url
        self.likes = likes or []
        self.views = views
    
    @classmethod
    def get_by_id(cls, blog_id):
        blog_data = mongo.db.blogs.find_one({"_id": ObjectId(blog_id)})
        if blog_data:
            return cls.from_dict(blog_data)
        return None
    
    @classmethod
    def get_by_author(cls, author_id):
        blogs_data = mongo.db.blogs.find({"author_id": author_id}).sort("created_at", -1)
        return [cls.from_dict(blog) for blog in blogs_data]
    
    @classmethod
    def get_by_user(cls, user_id, limit=None, skip=0):
        """Belirli bir kullanıcının blog yazılarını getirir, sayfalama için limit ve skip destekler"""
        query = mongo.db.blogs.find({"author_id": user_id}).sort("created_at", -1).skip(skip)
        if limit:
            query = query.limit(limit)
        return [cls.from_dict(blog) for blog in query]
    
    @classmethod
    def get_all(cls, limit=None, skip=0, sort_by="created_at", sort_order=-1):
        query = mongo.db.blogs.find().skip(skip).sort(sort_by, sort_order)
        if limit:
            query = query.limit(limit)
        return [cls.from_dict(blog) for blog in query]
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data.get('title'),
            content=data.get('content'),
            author_id=data.get('author_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=data.get('_id'),
            tags=data.get('tags', []),
            image_url=data.get('image_url'),
            likes=data.get('likes', []),
            views=data.get('views', 0)
        )
    
    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            "image_url": self.image_url,
            "likes": self.likes,
            "views": self.views
        }
    
    def save(self):
        now = datetime.utcnow()
        self.updated_at = now
        
        if self._id:
            # Update existing blog
            mongo.db.blogs.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "title": self.title,
                    "content": self.content,
                    "updated_at": now,
                    "tags": self.tags,
                    "image_url": self.image_url
                }}
            )
        else:
            # Insert new blog
            self.created_at = now
            blog_dict = self.to_dict()
            result = mongo.db.blogs.insert_one(blog_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.blogs.delete_one({"_id": ObjectId(self._id)})
            return True
        return False
    
    def increment_views(self):
        if self._id:
            self.views += 1
            mongo.db.blogs.update_one(
                {"_id": ObjectId(self._id)},
                {"$inc": {"views": 1}}
            )
        return self
    
    def add_like(self, user_id):
        if user_id not in self.likes:
            self.likes.append(user_id)
            if self._id:
                mongo.db.blogs.update_one(
                    {"_id": ObjectId(self._id)},
                    {"$addToSet": {"likes": user_id}}
                )
        return self
    
    def remove_like(self, user_id):
        if user_id in self.likes:
            self.likes.remove(user_id)
            if self._id:
                mongo.db.blogs.update_one(
                    {"_id": ObjectId(self._id)},
                    {"$pull": {"likes": user_id}}
                )
        return self 