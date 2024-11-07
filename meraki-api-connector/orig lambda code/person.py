import boto3
import os

TABLE_NAME = os.environ['TABLE_NAME']

class Person():
	def __init__(self,person_name,device_id,status):
		self.person_name = person_name
		self.device_id = device_id
		self.status = status

	def __repr__(self):
		return "This is a Person object. Attributes are: " + str(self.person_name) + ", " + str(self.device_id) + ", " + str(self.status) + ".\n"

	def get_person_name(self):
		return self.person_name

	def get_device_id(self):
		return self.device_id

	def get_status(self):
		return self.status

	def set_status(self,status):
		self.status = status

	def print_details(self,current_time,delta):
		print(f"Person is {self.get_person_name()}.\nEpoch is {current_time}.\nDelta is: {delta}.\n\n\n")

	def write_to_db(self):
		self.print_values_to_write()
		dynamodb = boto3.resource('dynamodb')
		table = dynamodb.Table(TABLE_NAME)
		r2 = table.update_item(Key={'person_name':self.get_person_name()},
								UpdateExpression='SET inorout = :val1',
								ExpressionAttributeValues={':val1':self.get_status()}
								)

	def print_values_to_write(self):
		print(f'I am ready to write to following values to the DB: person_name is {self.get_person_name()}, device_id is {self.get_device_id()}, status is {self.get_status()}')