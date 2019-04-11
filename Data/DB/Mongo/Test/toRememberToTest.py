
"""
Those under two lines are just set for use the __main___ into this file
"""
import sys
sys.path.append("../../../")

"""
Just for tests
"""
if __name__ == "__main__":
    mongo = Mongo()  # database='METEOR', collection='industries.employees'
    documents = mongo.get(query={'geocode_insee': 'FR89360'},
                          database='METEOR', collection='mainresidences.surfaces')
    [print(document) for document in documents]
