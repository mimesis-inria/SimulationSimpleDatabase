from typing import Dict, Any, Callable, Optional, List


class BaseObject:

    def __init__(self,
                 object_type: str,
                 object_name: str,
                 object_group: int):
        """
        The BaseObject is the common API for all backend Objects.

        :param object_type: Type of the Object.
        :param object_name: Name of the Object.
        :param object_group: Index of the group of the Object.
        """

        # Object identification
        self.type = object_type
        self.name = object_name
        self.group = object_group
        self.instance: Optional[Any] = None

        # Object data
        self._object_data: Dict[str, Any] = {}
        self._cmap_data: Dict[str, Any] = {}
        self._updated_fields: List[str] = []
        self.__updated_cmap: bool = False

        # Object specialization
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
        """
        Register data and create visual Object.

        :param data: Initial Object data.
        """

        # Register & sort data
        for field in ['colormap', 'scalar_field']:
            if field in data:
                self._cmap_data[field] = data.pop(field)
        self._object_data = data

        # Create the object
        self._create_object(self._object_data)

        # Apply the colormap
        if len(self._cmap_data.keys()) > 1:
            if len(self._cmap_data['scalar_field']) > 0:
                self.apply_cmap(self._cmap_data)

    def update_data(self,
                    data: Dict[str, Any]) -> None:
        """
        Register updated data.

        :param data: Updated Object data.
        """

        # Sort data
        cmap_data = {'scalar_field': data.pop('scalar_field')} if 'scalar_field' in data else {}
        cmap_data = cmap_data if 'scalar_field' in cmap_data and len(cmap_data['scalar_field']) > 0 else {}
        self.__updated_cmap = len(cmap_data.keys()) > 0

        # Register Object data
        self._updated_fields = []
        for key, value in data.items():
            self._object_data[key] = value
            self._updated_fields.append(key)
        for key, value in cmap_data.items():
            self._cmap_data[key] = value

    def update(self) -> None:
        """
        Update visual Object.
        """

        # Update the object
        if len(self._updated_fields) > 0 or self.type == 'Markers':
            self._update_object(self._object_data, self._updated_fields)

        # Apply the colormap
        if self.type != 'Text':
            if self.__updated_cmap or len(self._cmap_data['scalar_field']) > 0:
                self.apply_cmap(self._cmap_data)

    def apply_cmap(self,
                   data: Dict[str, Any]) -> None:
        """
        General colormap apply method.

        :param data: Colormap data.
        """

        raise NotImplementedError
