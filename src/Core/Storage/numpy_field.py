from peewee import Field
from numpy import ndarray
from pickle import loads


class NumpyField(Field):
    field_type = 'NUMPY'

    def db_value(self, value: ndarray):
        return value if value is None else value.dumps()

    def python_value(self, value: bytes):
        return value if value is None else loads(value)
