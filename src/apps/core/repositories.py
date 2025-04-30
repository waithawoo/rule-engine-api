from typing import List, Optional, Type, TypeVar, Generic
from django.db.models import Model, QuerySet

T = TypeVar('T', bound=Model)


class BaseRepository(Generic[T]):    
    model_class: Type[T]
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def _get_queryset(self) -> QuerySet:
        return self.model_class.objects.all()
    
    def get_by_id(self, id: int) -> Optional[T]:
        try:
            return self._get_queryset().get(pk=id)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by_filters(self, **filters) -> Optional[T]:
        try:
            return self._get_queryset().get(**filters)
        except self.model_class.DoesNotExist:
            return None
    
    def filter(self, **filters) -> QuerySet:
        return self._get_queryset().filter(**filters)
    
    def all(self) -> QuerySet:
        return self._get_queryset()
    
    def create(self, **kwargs) -> T:
        return self.model_class.objects.create(**kwargs)
    
    def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance: T) -> bool:
        instance.delete()
        return True
    
    def bulk_create(self, objects: List[T]) -> List[T]:
        return self.model_class.objects.bulk_create(objects)
