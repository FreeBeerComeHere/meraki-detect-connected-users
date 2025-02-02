# meraki-detect-connected-users
This project is an AWS SAM based application. For now, it provides a website through Lambda and API GW that shows if users are connected or not. The website is served through Cloudfront.

![](https://github.com/FreeBeerComeHere/meraki-detect-connected-users/blob/main/sample.png?raw=true)

## What it does
- Check the user's connection status using the Meraki API
- Update the DynamoDB table with the user's status
- Provide a website that indicates if users are online or offline (i.e. connected to the Meraki network or not)

## Steps
1. Deploy the `ACM certificate.yaml` template through Cloudformation so you can use it with Cloudfront:

```aws cloudformation create-stack --stack-name <name> --template-body file://<location>.yaml --parameters ParameterKey=CertificateFqdn,ParameterValue=<certificate CN> --region us-east-1```

2. Deploy the SAM template with the `sam deploy` command