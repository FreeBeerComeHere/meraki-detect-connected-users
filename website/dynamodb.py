import boto3

class DynamoDB:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        # Table(table_name)

    def get_item(self, name):
        response = self.table.get_item(
            Key={
                'person_name': name
                }
            )
        return response
