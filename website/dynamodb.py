import boto3

class DynamoDB:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        # Table(table_name)

    def get_item(self, name):
        response = self.table.get_item(
            Key={
                'personName': name
                }
            )
        return response
    
    def put_item(self, data):
        try:
            response = self.table.put_item(
            Item={
                'da_id': data['da_id'],
                'bestelling_id': data['b_id'],
                'amount': data['amount'],
            }
        )
        except Exception as e:
            print(e)
        else:
            return response
        return None
    
    def update_item(self, person_name, inorout):
        response = self.table.update_item(
            Key={
                'personName': person_name
            },
            UpdateExpression="set inorout = :inorout",
            ExpressionAttributeValues={
                ':inorout': inorout
            }
        )
        return response
    
    def scan(self):
        response = self.table.scan()
        return response