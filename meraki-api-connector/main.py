import mimetypes 
import boto3
import os
from person import Person

PERSONS_OF_INTEREST = os.environ['PERSONS_OF_INTEREST'].split(sep=' ')
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
LOCAL_PARENT_FOLDER = 'website_data' # What local folder contains the static files?
LOCAL_FOLDERS_TO_SYNC = ['img', 'src']
FILENAMES_TO_IGNORE = ['.DS_Store', 'index.html', 'index sample.html', 'person.ai']

def handler(event, context):
    print('######################################################')
    # print(event)
    initial_fill_s3()
    update_index_html_required = False # Keeps track of whether the index.html file needs to be updated
    person_states = [] # Keeps track of the state of each person
    
    for person in PERSONS_OF_INTEREST:
        p = Person(person)
        person_states.append(
            {
                'person_name': p.person_name,
                'in_or_out': p.new_status
                }
            )
        if p.state_has_changed:
            print('State has changed, we need to update the index.html file')
            update_index_html_required = True
                        
    if update_index_html_required:
        update_index_html(person_states)
    print('######################################################')
    return 0

def update_index_html(person_states):
    # Updates the index.html file
    print('Updating index.html file')
    print(person_states)
    with open(f'{LOCAL_PARENT_FOLDER}/src/index.html', 'r') as f:
        content = f.read()
        # print(content)
        for person in person_states:
            # print(person)
            string_to_replace = '{{status' + person.get('person_name') + '}}'
            # print(f'string to replace is: {string_to_replace}')
            content = content.replace(string_to_replace, person.get('in_or_out'))

    s3_client = boto3.client('s3') 
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key='index.html', Body=content, ContentType='text/html')

def initial_fill_s3():
    # Fills the S3 bucket with local files in case the bucket is empty
    # Get local files and folders
    local_directory_content = os.listdir(LOCAL_PARENT_FOLDER)
    
    s3_client = boto3.client('s3')  
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)    
    if not 'Contents' in response:
        # No contents found in the S3 bucket
        print("No contents found in the S3 bucket.")
        for local_content in local_directory_content:
            print(f'Creating directory "{local_content}" in bucket "{S3_BUCKET_NAME}"')
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=f'{local_content}/')
            # Adding local files to S3 bucket
            local_files = os.listdir(f'{LOCAL_PARENT_FOLDER}/{local_content}')
            print('local files:', local_files)
            for local_file in local_files:
                if local_file not in FILENAMES_TO_IGNORE:                
                    print(f'Uploading file "{local_content}/{local_file}" to bucket "{S3_BUCKET_NAME}"')
                    path = f'{LOCAL_PARENT_FOLDER}/{local_content}/{local_file}'
                    mime_type = mimetypes.guess_type(path)[0]
                    print(f'Uploading file "{local_content}/{local_file}" with mime type "{mime_type}" to bucket "{S3_BUCKET_NAME}"')
                    s3_client.put_object(Body=open(path, 'rb'), Bucket=S3_BUCKET_NAME, Key=f'{local_content}/{local_file}', ContentType=mime_type)
