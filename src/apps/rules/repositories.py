from apps.core.repositories import BaseRepository
from .models import Rule


class RuleRepository(BaseRepository[Rule]):
    def __init__(self):
        super().__init__(Rule)
    
