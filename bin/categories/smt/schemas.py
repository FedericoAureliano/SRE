import mongoengine
from mongoengine import *
import numpy as np


# MongoEngine schemas:
# ---------------------

class SMTInstance(Document):
    filename = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ['filename'], 'unique': True}
        ]
    }


class SMTResult(Document):
    program = StringField(required=True)
    nickname = StringField()
    # command = StringField()
    # version = StringField()
    instance = ReferenceField(SMTInstance, required=True)
    result = StringField(required=True)
    elapsed = FloatField(required=True)


# Parses all unique instances and writes them to the database
def write_instances(instances):
    mongoengine.connect('smt_database')

    for instance in instances:
        stripped_instance = instance.split("/", 1)[1]

        if not SMTInstance.objects(filename=stripped_instance):
            SMTInstance.objects(filename=stripped_instance).update_one(upsert=True, set__filename=stripped_instance)

    mongoengine.connection.disconnect()


# Function to parse data for analyze from the database
def read_database():
    data = {}

    mongoengine.connect('smt_database')
    parsed_result = np.dtype([('Instance', '<U14'), ('Result', '<U7'), ('Time', '<f8')])
    for result in SMTResult.objects():

        new_data = np.array([(result.instance.filename, result.result, result.elapsed)], dtype=parsed_result)

        if result.nickname in data:
            data[result.nickname] = np.append(data[result.nickname], new_data)
        else:
            data[result.nickname] = new_data

    return data