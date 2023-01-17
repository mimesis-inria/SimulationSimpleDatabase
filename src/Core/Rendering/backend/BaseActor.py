from typing import Dict, Any, Callable, Optional, List


class BaseActor:

    def __init__(self,
                 actor_type: str,
                 actor_name: str,
                 actor_group: int):

        # Actor identification
        self.type = actor_type
        self.name = actor_name
        self.group = actor_group

        # Actor data
        self._object_data: Dict[str, Any] = {}
        self._cmap_data: Dict[str, Any] = {}
        self._updated_fields: List[str] = []

        # Actor specialization
        self._create_object: Optional[Callable] = None
        self._update_object: Optional[Callable] = None
        self._cmap_object: Optional[Callable] = None
        
    @property
    def object_data(self) -> Dict[str, Any]:
        return self._object_data.copy()
    
    @property
    def cmap_data(self) -> Dict[str, Any]:
        return self._cmap_data.copy()
    
    @property
    def updated_fields(self) -> List[str]:
        return self._updated_fields.copy()

    def create(self,
               data: Dict[str, Any]) -> None:

        # Sort data
        cmap_data = {}
        for field in ['colormap', 'scalar_field']:
            if field in data:
                cmap_data[field] = data.pop(field)

        # Register Actor data
        self._object_data = data
        self._cmap_data = cmap_data

        # Create the object
        self._create_object(self._object_data)

        # Apply the colormap
        if len(cmap_data.keys()) > 1:
            if len(self._cmap_data['scalar_field']) > 0:
                self.apply_cmap(self._cmap_data)

    def update(self,
               data: Dict[str, Any]) -> None:

        # Sort data
        cmap_data = {'scalar_field': data.pop('scalar_field')} if 'scalar_field' in data else {}

        # Register Actor data
        self._updated_fields = []
        for key, value in data.items():
            self._object_data[key] = value
            self._updated_fields.append(key)
        for key, value in cmap_data.items():
            self._cmap_data[key] = value

        # Update the object
        if len(data.keys()) > 0 or self.type == 'Markers':
            self._update_object(self._object_data, self._updated_fields)

        # Apply the colormap
        if self.type != 'Text':
            if len(cmap_data.keys()) > 0 or len(self._cmap_data['scalar_field']) > 0:
                self.apply_cmap(self._cmap_data)

    def apply_cmap(self,
                   data: Dict[str, Any]) -> None:

        raise NotImplementedError
