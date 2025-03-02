from bson.objectid import ObjectId
from datetime import datetime
from app.extensions import mongo

class Enrollment:
    def __init__(self, user_id=None, course_id=None, status="active", progress=0, _id=None):
        self.user_id = user_id
        self.course_id = course_id
        self.status = status  # active, completed, cancelled
        self.progress = progress  # 0-100 yüzde olarak ilerleme
        self._id = _id
        self.enrolled_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        
    @classmethod
    def get_by_id(cls, enrollment_id):
        enrollment_data = mongo.db.enrollments.find_one({"_id": ObjectId(enrollment_id)})
        if enrollment_data:
            return cls.from_dict(enrollment_data)
        return None
    
    @classmethod
    def get_by_user_and_course(cls, user_id, course_id):
        enrollment_data = mongo.db.enrollments.find_one({
            "user_id": user_id,
            "course_id": course_id
        })
        if enrollment_data:
            return cls.from_dict(enrollment_data)
        return None
    
    @classmethod
    def get_by_user(cls, user_id):
        cursor = mongo.db.enrollments.find({"user_id": user_id})
        return [cls.from_dict(enrollment_data) for enrollment_data in cursor]
    
    @classmethod
    def get_by_course(cls, course_id):
        cursor = mongo.db.enrollments.find({"course_id": course_id})
        return [cls.from_dict(enrollment_data) for enrollment_data in cursor]
    
    @classmethod
    def get_count_by_course(cls, course_id):
        return mongo.db.enrollments.count_documents({"course_id": course_id})
    
    @classmethod
    def from_dict(cls, data):
        enrollment = cls()
        enrollment.user_id = data.get('user_id')
        enrollment.course_id = data.get('course_id')
        enrollment.status = data.get('status', 'active')
        enrollment.progress = data.get('progress', 0)
        enrollment.enrolled_at = data.get('enrolled_at', datetime.utcnow())
        enrollment.last_accessed = data.get('last_accessed', datetime.utcnow())
        enrollment._id = data.get('_id')
        return enrollment
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "course_id": self.course_id,
            "status": self.status,
            "progress": self.progress,
            "enrolled_at": self.enrolled_at,
            "last_accessed": self.last_accessed
        }
    
    def save(self):
        # Son erişim zamanını güncelle
        self.last_accessed = datetime.utcnow()
        
        if self._id:
            # Update existing enrollment
            mongo.db.enrollments.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": self.to_dict()}
            )
        else:
            # Insert new enrollment
            enrollment_dict = self.to_dict()
            result = mongo.db.enrollments.insert_one(enrollment_dict)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        if self._id:
            mongo.db.enrollments.delete_one({"_id": ObjectId(self._id)})
            return True
        return False
    
    def update_progress(self, new_progress):
        self.progress = new_progress
        if self.progress >= 100:
            self.status = "completed"
        self.save()
        return self 