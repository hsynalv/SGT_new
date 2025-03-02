from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class Lesson:
    def __init__(self, title=None, description=None, video_url=None, course_id=None, 
                 order=None, duration=None, _id=None):
        self.title = title
        self.description = description
        self.video_url = video_url
        self.course_id = course_id
        self.order = order or 0
        self.duration = duration
        self._id = _id
        self.created_at = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, lesson_id):
        lesson_data = mongo.db.lessons.find_one({"_id": ObjectId(lesson_id)})
        if lesson_data:
            return cls.from_dict(lesson_data)
        return None
    
    @classmethod
    def get_by_course(cls, course_id):
        cursor = mongo.db.lessons.find({"course_id": course_id}).sort("order", 1)
        return [cls.from_dict(lesson_data) for lesson_data in cursor]
    
    @classmethod
    def from_dict(cls, data):
        lesson = cls()
        lesson.title = data.get('title')
        lesson.description = data.get('description')
        lesson.video_url = data.get('video_url')
        lesson.course_id = data.get('course_id')
        lesson.order = data.get('order', 0)
        lesson.duration = data.get('duration')
        lesson.created_at = data.get('created_at', datetime.utcnow())
        lesson._id = data.get('_id')
        return lesson
    
    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "video_url": self.video_url,
            "course_id": self.course_id,
            "order": self.order,
            "duration": self.duration,
            "created_at": self.created_at
        }
    
    def save(self):
        if self._id:
            # Update existing lesson
            mongo.db.lessons.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new lesson
            lesson_dict = self.to_dict()
            result = mongo.db.lessons.insert_one(lesson_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.lessons.delete_one({"_id": ObjectId(self._id)})
            return True
        return False 