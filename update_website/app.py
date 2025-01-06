import base64
import os
from dynamodb import DynamoDB

PERSONS_OF_INTEREST = os.environ['PERSONS_OF_INTEREST'].split(sep=' ')
TABLE_NAME = os.environ['TABLE_NAME']

def update_website_on_s3(event, context):
    print(f'Dumping the event describing the ')
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
    
def render_website(event, context):
    # print(event)
    with open('src/index.html', 'r') as f:
        html_code = f.read()
    
    ddb = DynamoDB(TABLE_NAME)
    for person in PERSONS_OF_INTEREST:
        out = ddb.get_item(person)
        # print(out)
        # Extract status
        try:
            status = out.get('Item').get('in_or_out')
            print(status)
        except Exception as e:
            # Person not found in DDB
            print(e)
            status = 'out'
        else:
            # Create proper inorout string
            inorout_string = f'status{person}' # This is the text we will look for in the HTML
            if status == 'in':
                html_code = html_code.replace('{{'+inorout_string+'}}', ' in') # If person is connected to the network, add " in" to HTML class
            else:
                html_code = html_code.replace('{{'+inorout_string+'}}', '')

    try:
        raw_path = event.get('rawPath')
    except Exception as e:
        print(event)
        # rawPath not set, return 404
        return {
            'statusCode': 404,
            'body': 'Not Found',
            }
    else:
        if raw_path == '/icons/person.png':
            return {
                'statusCode': 200,
                'headers': {'content-type': 'image/png'},
                'body': base64.b64encode(open('img/person.png', 'rb').read()).decode('utf8'),
                'isBase64Encoded': True
            }
        elif raw_path == '/styles.css':
            return {
                'statusCode': 200,
                'headers': {'content-type': 'text/css'},
                'body': open('src/styles.css', 'rb').read(),
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'content-type': 'text/html'},
                'body': html_code,
                }