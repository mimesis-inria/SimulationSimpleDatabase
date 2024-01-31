from typing import Union, Dict, Any
import json
import csv
from peewee import Query
from datetime import datetime
from numpy import ndarray


def default_format(o: Any):
    if isinstance(o, datetime):
        return o.isoformat()
    elif isinstance(o, ndarray):
        return o.tolist()


class Exporter:

    @classmethod
    def export_json(cls,
                    filename: str,
                    query: Union[Dict[str, Any], Query]):

        file = open(filename, 'w')
        json.dump(query, file, default=default_format)
        file.close()

    @classmethod
    def export_csv(cls,
                   filename: str,
                   query: Union[Dict[str, Any], Query]):

        with open(filename, 'w') as file:
            writer = csv.writer(file)
            t = query.execute()
            t.initialize()
            if getattr(t, 'columns', None):
                writer.writerow([column for column in t.columns])
            for row in t:
                writer.writerow(row)
