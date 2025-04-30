from django.db.models import QuerySet

from .repositories import UserRepository
from .models import User


class UserService:
    def __init__(self):
        self.repository = UserRepository()
    
    def all(self) -> QuerySet:
        return self.repository.all()
    
    def create(self, **kwargs) -> User:
        return self.repository.create(**kwargs)
