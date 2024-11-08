import os
from person import Person

PERSONS_OF_INTEREST = os.environ['PERSONS_OF_INTEREST'].split(sep=' ')
def handler(event, context):
    print('######################################################')
    # print(event)
    for person in PERSONS_OF_INTEREST:
        Person(person)        
    print('######################################################')
    return 0