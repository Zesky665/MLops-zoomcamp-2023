import json
import logging
import os
import sys
from time import sleep
import boto3
from botocore.exceptions import ClientError
import requests

logger = logging.getLogger(__name__)

def create_client(type: str):
    """
    Creates a boto3 client.
    """
    
    if type not in ['ec2', 'security_groups', 'key_pairs', 's3', 'iam']:
        logging.exception("Incorrect client type.")
        sys.exit(1)
    else:
        return boto3.client(type)

def create_resource(type: str):
    """
    Creates a boto3 resource.
    """
    
    if type not in ['ec2', 'security_groups', 'key_pairs', 's3', 'iam']:
        logging.exception("Incorrect client type.")
        sys.exit(1)
    else:
        return boto3.resource(type)
    
def create_instance(key_name: str):
    """
    Creates an instance.
    """
    ec2 = create_resource("ec2")
    
    ImageId="ami-0ec7f9846da6b0f61"
    InstanceType="t2.micro"
    
    try:
        instance = ec2.create_instances(
            ImageId=ImageId,
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            InstanceType=InstanceType
        )
        print(instance[0])
        return instance[0]
    except ClientError as err:
                logging.error(
                    "Couldn't create instance with image %s, instance type %s."
                    "Here's why: %s: %s", ImageId, InstanceType,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise

def save_private_key_to_file(key_material: str, key_name: str):
    """
    Creates a private key file locally.
    """
    key_file_name = f'{key_name}.pem'
    with open(key_file_name, "w") as f:
        f.write(key_material)
        
def check_if_key_exists(key_name: str):
    """
    Checks if a key exists.
    """
    ec2 = create_client("ec2")
    try:
        response = ec2.describe_key_pairs(
            KeyNames=[key_name]
        )
        print(response)
        if response['KeyPairs'] == []:
            return False
        else:
            return True
    except ClientError as err:
        logger.error(
            "Couldn't check if key %s exists. Here's why: %s: %s", key_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise


def create_key_pair(key_name: str):
    """
    Creates a private key pair.
    """
    ec2 = create_client("ec2")
    if check_if_key_exists(key_name):
        print("Key already exists")
    else:
        try:
            response = ec2.create_key_pair(
            KeyName=key_name)

            print(response)
            save_private_key_to_file(response['KeyMaterial'], key_name)
        except ClientError as err:
                logger.error(
                    "Couldn't create key %s. Here's why: %s: %s", key_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise

def allocate_elastic_ip_address():
    """
    Allocates an elastic IP address.
    """
    ec2 = create_client("ec2")
    allocation = ec2.allocate_address(
    Domain='vpc',
    TagSpecifications=[
        {
            'ResourceType': 'elastic-ip',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'mlops-elastic-ip'
                },
            ]
        },
    ]
)
    return allocation['AllocationId']

def associate_elastic_ip_address(allocation_id: str, instance_id: str):
    """
    Associates an elastic IP address.
    """
    ec2 = create_client("ec2")
    
    while check_instance_status(instance_id) is False:
        print("Waiting for instance to be ready...")
        sleep(5)
        
    response = ec2.associate_address(
    InstanceId=instance_id,
    AllocationId=allocation_id
)

    return response

def get_my_ip_address():
    """
    Gets my public IP address.
    Returns:
        my_ip (str): my public IP address.
    """
    url = "https://api.my-ip.io/ip"
    ip_response = requests.request("GET", url)
    my_ip = (ip_response.text + "/32")
    
    return my_ip

def update_security_group(sg_id: str):
    """
    Updates the security group to allow ssh from local PC.
    """
    ec2 = create_client("ec2")
    my_ip = get_my_ip_address()
    try:
        ip_permissions = [{
            # SSH ingress open to only the specified IP address.
            'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
            'IpRanges': [{'CidrIp': f'{my_ip}'}]}]
        response = ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)
        return response
    except ClientError as err:
            logger.error(
                "Couldn't authorize inbound rules for %s. Here's why: %s: %s",
                sg_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
    
def create_status_file(instance_id: str, key_pair_name: str, allocation_id: str):
    """
    Creates a file that contains the instance ID.
    """
    with open("status.json", "w") as f:
        dict = {
            "instance_id": instance_id,
            "key_pair_name": key_pair_name,
            "allocation_id": allocation_id
        }
        json_object = json.dumps(dict, indent = 4) 
        f.write(json_object)
    
def get_instance_id():
    """
    Get the instance id from the status file.
    """
    try:
        # JSON file
        f = open ('/Users/zharec/MLops-zoomcamp-2023/Week_1/status.json', "r")
        
        # Reading from file
        data = json.loads(f.read())
        
        if "instance_id" in data:
            return data['instance_id']
        else:
            logging.exception("Instance Id not found in status file.")
    except FileNotFoundError:
        logging.exception("File not found.")
        
def stop_instance(instance_id):
    """
    Stop the instance.
    """
    try:
        ec2 = boto3.client('ec2')
        ec2.stop_instances(InstanceIds=[instance_id], Hibernate=False)
    except Exception:
        logging.exception("Something went wrong with the instance.")
        
def start_instance(instance_id):
    """
    Start the instance.
    """
    try:
        ec2 = boto3.client('ec2')
        ec2.start_instances(InstanceIds=[instance_id])
    except Exception:
        logging.exception("Something went wrong with the instance.")
    
def check_instance_status(instance_id):
    """
    Check the status of the instance.
    """
    try:
        ec2 = create_resource("ec2")
        instance = ec2.Instance(instance_id)
        if instance.state['Name'] == 'running':
            return True
        else:
            return False
    except Exception:
        logging.exception("Something went wrong with the instance.")
        return False
        
if __name__ == '__main__':
    
    if os.path.isfile("/Users/zharec/MLops-zoomcamp-2023/Week_1/status.json") == False:
        try:
            key_name = 'foundry-key-pair'
            create_key_pair(key_name)
            allocation_id=allocate_elastic_ip_address()
            instance = create_instance(key_name)
            associate_elastic_ip_address(allocation_id, instance.instance_id)
            update_security_group(instance.security_groups[0].get("GroupId"))
            create_status_file(instance.instance_id, key_name, allocation_id)
            print("Successfull setup")
            
        except Exception:
            logging.exception("Something went wrong with the setup.")
    else:
        try:
            instance_id = get_instance_id()
            print(instance_id)
            
            if check_instance_status(instance_id):
                print("Instance is running.")
                print("Would you like to stop it? y/n")
                answer = input()
                if answer == "y":
                    stop_instance(instance_id)
                    print("Stopping instance.")
            else:   
                print("Instance is stopped.")
                print("Would you like to start it? y/n")
                answer = input()
                if answer == "y":
                    start_instance(instance_id)
                    print("Starting instance.")
            
        except Exception:
            logging.exception("Something went wrong with the cleanup.")
    
    print("Done")