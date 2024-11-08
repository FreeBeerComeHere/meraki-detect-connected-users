import time
from dynamodb import DynamoDB
import boto3
import os
import requests
import traceback

TABLE_NAME = os.environ['TABLE_NAME']
MERAKI_API_KEY_SECRET_NAME = os.environ['MERAKI_API_KEY_SECRET_NAME']
MERAKI_API_KEY_SECRET_REGION = os.environ['MERAKI_API_KEY_SECRET_REGION']
MERAKI_NETWORK_ID = os.environ['MERAKI_NETWORK_ID']
MERAKI_API_BASE_URL = f'https://api.meraki.com/api/v1/networks/{MERAKI_NETWORK_ID}/clients/' # Changed from v0 to v1 on 28Jan24 due to Meraki v0 deprecation
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
WAIT_TIME_SECONDS=300 # This is the amount of seconds to wait before changing a persons status. Higher = fewer false positives
EPOCH_TIME = int(time.time())

class Person():
    def __init__(self,person_name):
        self.person_name = person_name
        self.ddb = DynamoDB(TABLE_NAME)
        # Search person in DDB
        response = self.ddb.get_item(self.person_name)
        if 'Item' not in response:
            # Person does not exist in DDB
            print(f'Person "{self.person_name}" does not exist in DDB')
        else:
            print(f'Dumping DDB response: {response}')
            self.device_id = response.get('Item').get('device_id')
            self.old_status = response.get('Item').get('in_or_out')
            self.delta = 0
            self.new_status = self.get_person_connected_state_from_meraki()
            # Check if old and new status match
            if not self.old_status == self.new_status:
                print(f'PING PING Status change detected for "{self.person_name}": {self.old_status} does not equal {self.new_status}')
                # print(f'delta is "{delta}"')
                # Send new status to DDB
                self.write_to_db()
            else:
                print(f'No status change, old status is "{self.old_status}" and new status is "{self.new_status}", delta is "{self.delta}".')
            

    def __repr__(self):
        return "This is a Person object. Attributes are: " + str(self.person_name) + ", " + str(self.device_id) + ", " + str(self.status) + ".\n"

    def get_person_connected_state_from_meraki(self):
        # Connect to Meraki API and check person's new status
        meraki_url = MERAKI_API_BASE_URL + self.device_id
        http_headers = {'X-Cisco-Meraki-API-Key': get_secret(),'Connection':'close'}
        try:
            meraki_response = requests.get(url=meraki_url,headers=http_headers)
        except ValueError as decode1_error:
            print(f'An error occurred decoding (1) the JSON. Error details:\n{decode1_error}\nResponse details:\n{meraki_response}')
            publish_via_sns(f'{traceback.format_exc()}\n{decode1_error}')
        except RequestsJSONDecodeError as decode2_error:
            print(f'An error occurred decoding (2) the JSON. Error details:\n{decode2_error}\nResponse details:\n{meraki_response}')
            publish_via_sns(f'{traceback.format_exc()}\n{decode2_error}')
        except Exception as e:
            print(f'An undefined error occurred. Either the Meraki API is unreachable or we couldn\'t parse Meraki\'s response. Error details (Meraki response below, if any):\n{e}\nMeraki response:\n{meraki_response}')
            publish_via_sns(f'{traceback.format_exc()}\n{e}')
        else:
            # No error occurred, parse Meraki's response
            try:
                response_content = meraki_response.json()
                last_seen = response_content.get('lastSeen')
            except Exception as e:
                print(f'An error occurred connecting to the Meraki API or analysing the Meraki API output.')
            else:
                print(f'Lastseen value return by Meraki for "{self.person_name}" is "{last_seen}"')
                if not type(last_seen) == int:
                    print(f'Lastseen value is not an integer, it is "{last_seen}". Setting last_seen to 0.')
                    last_seen = 0

                if last_seen > 2000: # yes, the returned value from the API is usable
                    print(f'Calculating delta for person "{self.person_name}": current time {EPOCH_TIME} - last_seen {last_seen} equals ',end='')
                    self.delta = EPOCH_TIME - last_seen
                    print(f'delta {self.delta}')
                    if self.delta > WAIT_TIME_SECONDS:
                        # Person is not connected
                        return 'out'
                    else:
                        # Person is connected
                        return 'in'
        return None
    def get_person_name(self):
        return self.person_name

    def get_device_id(self):
        return self.device_id

    def get_status(self):
        return self.status

    def set_status(self,status):
        self.status = status

    def write_to_db(self):
        self.print_values_to_write()
        response = self.ddb.update_item(self.person_name,self.new_status)
        print(f'Dump DDB response: {response}')

    def print_values_to_write(self):
        print(f'I am ready to write to following values to the DB: person_name is {self.person_name}, device_id is {self.device_id}, status is {self.new_status}')
        
def publish_via_sns(errordetails):
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject='Meraki-detect-connected-users encountered an error',
        Message=f'Meraki-detect-connected-users encountered the following error:\n{errordetails}',
    )
def get_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=MERAKI_API_KEY_SECRET_REGION
        )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=MERAKI_API_KEY_SECRET_NAME
            )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = eval(get_secret_value_response['SecretString'])

    secret = secret.get('Meraki-API-key')
    return secret
