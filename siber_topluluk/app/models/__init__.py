# Models paketi
# Bu dosya models klasörünün bir Python paketi olarak tanınmasını sağlar. 

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.ctf import Challenge, Submission, Badge, UserBadge, ChallengeCategory, ChallengeDifficulty 