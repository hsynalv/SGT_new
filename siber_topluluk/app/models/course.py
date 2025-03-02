from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class Course:
    def __init__(self, title=None, description=None, image_url=None, instructor=None, 
                 level=None, tags=None, created_by=None, _id=None):
        self.title = title
        self.description = description
        self.image_url = image_url
        self.instructor = instructor
        self.level = level
        self.tags = tags or []
        self.created_by = created_by
        self._id = _id
        self.created_at = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, course_id):
        course_data = mongo.db.courses.find_one({"_id": ObjectId(course_id)})
        if course_data:
            return cls.from_dict(course_data)
        return None
    
    @classmethod
    def get_all(cls, skip=0, limit=0):
        cursor = mongo.db.courses.find().sort("created_at", -1).skip(skip).limit(limit)
        return [cls.from_dict(course_data) for course_data in cursor]
    
    @classmethod
    def from_dict(cls, data):
        course = cls()
        course.title = data.get('title')
        course.description = data.get('description')
        course.image_url = data.get('image_url')
        course.instructor = data.get('instructor')
        course.level = data.get('level')
        course.tags = data.get('tags', [])
        course.created_by = data.get('created_by')
        course.created_at = data.get('created_at', datetime.utcnow())
        course._id = data.get('_id')
        return course
    
    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "instructor": self.instructor,
            "level": self.level,
            "tags": self.tags,
            "created_by": self.created_by,
            "created_at": self.created_at
        }
    
    def save(self):
        if self._id:
            # Update existing course
            mongo.db.courses.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new course
            course_dict = self.to_dict()
            result = mongo.db.courses.insert_one(course_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.courses.delete_one({"_id": ObjectId(self._id)})
            # Ayrıca ilgili dersler ve kayıtları da siliyoruz
            mongo.db.lessons.delete_many({"course_id": str(self._id)})
            mongo.db.enrollments.delete_many({"course_id": str(self._id)})
            return True
        return False 