import boto3
import os
from dynamodb import DynamoDB


class Person():
    def __init__(self,person_name,device_id,last_seen,status):
        self.person_name = person_name
        self.device_id = device_id
        self.last_seen = last_seen
        self.status = status
        self.new_last_seen = 0
        

    def __repr__(self):
        return "This is a Person object. Props: " + str(self.personName) + ", " + str(self.deviceId) + ", " + str(self.oldLastSeen) + ", " + str(self.status) + ".\n"

    def set_last_seen(self,last_seen):
        self.last_seen = last_seen
  
    def set_status(self,status):
        self.status = status

    def print_details(self,current_time,delta):
        print(f'Person is {self.person_name}.\nLast_seen is {self.last_seen}.\nEpoch is {current_time}.\nDelta is: {delta}.\n\n\n')
  
    def write_to_db(self):
        self.print_values_to_write()
        self.ddb.update_item(self.person_name,self.status)

    def print_values_to_write(self):
        print(f'I am ready to write to following values to the DB:\nperson_name is {self.person_name}\ndevice_id is {self.device_id}\nlast_seen is {self.last_seen}\nstatus is {self.status}')