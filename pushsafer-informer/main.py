import os
import requests
import boto3
from botocore.exceptions import ClientError

PUSHSAFER_SECRET_NAME = os.environ['PUSHSAFER_SECRET_NAME']
PUSHSAFER_SECRET_REGION = os.environ['PUSHSAFER_SECRET_REGION']

def handler(event, context):
    print(f'Received event: {event}')
    for record in event['Records']:
        if record['eventName'] == 'MODIFY':
            personName = record['dynamodb']['NewImage']['person_name']['S']
            state = record['dynamodb']['NewImage']['in_or_out']['S']
            message = personName + " is "+ state
            url = 'https://www.pushsafer.com/api'
            text = 'ERROR'
            if state == 'in':
                text = 'arrived'
            elif state == 'out':
                text = 'left'
            post_fields = {
                "t" : 'Person has ' + text,
                "m" : message,
                "s" : "sound",
                "v" : 3,
                "i" : 81,
                "c" : '#FF0000',
                "d" : '26406',
                "u" : 'https://www.pushsafer.com',
                "ut" : 'Open Pushsafer',
                "k" : getSecret(),
                "p" : 'picture'
                #"p" : 'data:image/jpeg;base64,'+str(image1.decode('ascii')),
                #"p2" : 'data:image/png;base64,'+str(image2.decode('ascii'))
            }
            
            resp = requests.post(url=url, data=post_fields)
            print(resp)
            # print(resp.text)

def getSecret():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=PUSHSAFER_SECRET_REGION
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=PUSHSAFER_SECRET_NAME
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    return eval(get_secret_value_response['SecretString']).get('Pushsafer-API-key')