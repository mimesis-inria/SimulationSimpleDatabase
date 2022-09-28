import json
import csv
from datetime import datetime
from numpy import ndarray


class Exporter:

    @classmethod
    def export(cls, filename, query):
        pass


class ExporterJson(Exporter):

    @staticmethod
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, ndarray):
            return o.tolist()

    @classmethod
    def export(cls, filename, query):
        file = open(filename, 'w')
        json.dump(query, file, default=cls.default)
        file.close()


class ExporterCSV(Exporter):

    @classmethod
    def export(cls, filename, query):
        file = open(filename, 'w')
        writer = csv.writer(file)
        t = query.execute()
        t.initialize()
        if getattr(t, 'columns', None):
            writer.writerow([column for column in t.columns])
        for row in t:
            writer.writerow(row)
        file.close()
