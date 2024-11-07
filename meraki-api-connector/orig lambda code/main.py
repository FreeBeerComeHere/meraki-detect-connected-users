import os
import time
import json
import boto3
import requests
from person import Person
from botocore.exceptions import ClientError
import traceback

TABLE_NAME = os.environ['TABLE_NAME']
MERAKI_API_KEY_SECRET_NAME = os.environ['MERAKI_API_KEY_SECRET_NAME']
MERAKI_API_KEY_SECRET_REGION = os.environ['MERAKI_API_KEY_SECRET_REGION']
MERAKI_NETWORK_ID = os.environ['MERAKI_NETWORK_ID']
MERAKI_API_BASE_URL = f'https://api.meraki.com/api/v1/networks/{MERAKI_NETWORK_ID}/clients/' # Changed from v0 to v1 on 28Jan24 due to Meraki v0 deprecation
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
WAIT_TIME_SECONDS=300 # This is the amount of seconds to wait before changing a persons status. Higher = fewer false positives
EPOCH_TIME = int(time.time())

def lambda_handler(event, context):
    print('######################################################')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    items = response['Items']

    arr = []
    currentTime = int(time.time())

    for device in items:
        person_name = device.get('person_name')
        device_id = device.get('device_id')
        status = device.get('inorout')
        new_person = Person(person_name=person_name,device_id=device_id,status=status)
        arr.append(new_person)

    for person in arr:
        print('#############')
        print(f'Starting for loop with new person: {person}')
        # Build HTTP request content
        MerakiURL = MERAKI_API_BASE_URL + person.getDeviceId()
        HTTPheaders = {'X-Cisco-Meraki-API-Key': getSecret(),'Connection':'close'}
    
        try:
            meraki_response = requests.get(url=MerakiURL,headers=HTTPheaders)
        except ValueError as decode1_error:
            print(f'An error occurred decoding (1) the JSON. Error details:\n{decode1_error}\nResponse details:\n{meraki_response}')
            # publish_via_sns(decode1_error)
            publish_via_sns(f'{traceback.format_exc()}\n{decode1_error}')
        except RequestsJSONDecodeError as decode2_error:
            print(f'An error occurred decoding (2) the JSON. Error details:\n{decode2_error}\nResponse details:\n{meraki_response}')
            # publish_via_sns(decode2_error)
            publish_via_sns(f'{traceback.format_exc()}\n{decode2_error}')
        except Exception as e:
            print(f'An undefined error occurred. Either the Meraki API is unreachable or we couldn\'t parse Meraki\'s response. Error details (Meraki response below, if any):\n{e}\nMeraki response:\n{meraki_response}')
            publish_via_sns(f'{traceback.format_exc()}\n{e}')
        else:
            content = meraki_response.json()
            lastSeen = content.get('lastSeen')
            print(f'Lastseen value return by Meraki for "{person.getPersonName()}" is "{lastSeen}"')
            if not isinstance(lastSeen, int):
                lastSeen = 0
            print(f'Getting oldStatus for {person.getPersonName()}: {person.getStatus()}')
            oldStatus = person.getStatus()
    
            if lastSeen > 2000: # yes, the returned value from the API is usable
                print(f'Calculating delta from {person.getPersonName()}: currentTime {currentTime} - lastSeen {lastSeen} equals ',end='')
                delta = currentTime - lastSeen
                print(f'delta {delta}')
                #person.printDetails(currentTime,delta)
                if delta > WAIT_TIME_SECONDS:
                    # Person has left
                    newStatus = 'out'
                    person.setStatus(newStatus)
                    if not oldStatus == newStatus:
                        print(f'delta is "{delta}"')
                        print(f'{oldStatus} does not equal {newStatus}')
                        print(f'PING PING User {person.getPersonName()} has left.')
                        person.writeToDb()
                    else:
                        print(f'No status change, old status is "{oldStatus}" and new status is "{newStatus}", delta is "{delta}".')
                        
                elif delta <= WAIT_TIME_SECONDS:
                    # Person is home
                    newStatus = 'in'
                    person.setStatus(newStatus)
                    if not oldStatus == newStatus:
                        print(f'delta is "{delta}"')
                        print(f'{oldStatus} does not equal {newStatus}')
                        print(f'PING PING User {person.getPersonName()} is home.')
                        person.writeToDb()
                    else:
                        print(f'No status change, old status is "{oldStatus}" and new status is "{newStatus}", delta is "{delta}".')
    
                        
                else:
                    print(f'ERROR: delta "{delta}" is not greater or smaller than WAIT_TIME_SECONDS "{WAIT_TIME_SECONDS}". This should not be happening!')
            else:
                print(f'The returned value from Meraki "{lastSeen}" is unusable!')
            print('#############')
    
        
    print('######################################################')
    return 0


def getSecret():
    # Create a Secrets Manager client
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
    newSecret = secret.get('Meraki-API-key')
    #newSecret now contains the API key
    return newSecret
    
def publish_via_sns(errordetails):
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject='Meraki-detect-connected-users encountered an error',
        Message=f'Meraki-detect-connected-users encountered the following error:\n{errordetails}',
    )