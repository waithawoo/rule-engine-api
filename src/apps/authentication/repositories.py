from apps.core.repositories import BaseRepository
from .models import User


class UserRepository(BaseRepository[User]):    
    def __init__(self):
        super().__init__(User)
    
    def create(self, email: str, password: str, **kwargs) -> User:
        return User.objects.create_user(email=email, password=password, **kwargs)
