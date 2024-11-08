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
        
    def update_item(self, person_name, new_status):
        response = self.table.update_item(
            Key={
                'person_name': person_name
            },
            UpdateExpression="set in_or_out = :in_or_out",
            ExpressionAttributeValues={
                ':in_or_out': new_status
            }
        )
        return response
    
    def scan(self):
        response = self.table.scan()
        return response