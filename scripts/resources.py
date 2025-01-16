import os
import boto3
from botocore.exceptions import ClientError
import json
from datetime import datetime

def get_all_regions():
    """Get list of all AWS regions"""
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    return regions

def get_ec2_instances(region):
    """Get details of EC2 instances in specified region"""
    ec2_client = boto3.client('ec2', region_name=region)
    instances = []
    try:
        response = ec2_client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'LaunchTime': instance['LaunchTime'].strftime("%Y-%m-%d %H:%M:%S"),
                    'Tags': instance.get('Tags', [])
                })
    except ClientError as e:
        print(f"Error getting EC2 instances in {region}: {e}")
    return instances

def get_rds_instances(region):
    """Get details of RDS instances in specified region"""
    rds_client = boto3.client('rds', region_name=region)
    instances = []
    try:
        response = rds_client.describe_db_instances()
        for instance in response['DBInstances']:
            instances.append({
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'DBInstanceClass': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus']
            })
    except ClientError as e:
        print(f"Error getting RDS instances in {region}: {e}")
    return instances

def get_vpcs(region):
    """Get details of VPCs in specified region"""
    ec2_client = boto3.client('ec2', region_name=region)
    vpcs = []
    try:
        response = ec2_client.describe_vpcs()
        for vpc in response['Vpcs']:
            vpcs.append({
                'VpcId': vpc['VpcId'],
                'CidrBlock': vpc['CidrBlock'],
                'IsDefault': vpc['IsDefault'],
                'State': vpc['State'],
                'Tags': vpc.get('Tags', [])
            })
    except ClientError as e:
        print(f"Error getting VPCs in {region}: {e}")
    return vpcs

def get_s3_buckets():
    """Get details of S3 buckets (S3 is global)"""
    s3_client = boto3.client('s3')
    buckets = []
    try:
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            buckets.append({
                'Name': bucket['Name'],
                'CreationDate': bucket['CreationDate'].strftime("%Y-%m-%d %H:%M:%S")
            })
    except ClientError as e:
        print(f"Error getting S3 buckets: {e}")
    return buckets

def main():
    # Get all regions
    regions = get_all_regions()
    
    # Dictionary to store all resources
    all_resources = {}
    
    # Get S3 buckets (global service)
    all_resources['S3_Buckets'] = get_s3_buckets()
    
    # Get resources for each region
    for region in regions:
        print(f"Scanning region: {region}")
        all_resources[region] = {
            'EC2_Instances': get_ec2_instances(region),
            'RDS_Instances': get_rds_instances(region),
            'VPCs': get_vpcs(region)
        }
    
    # Save results to a JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aws_resources_{timestamp}.json"
    
    # Get the absolute path to save the file
    current_dir = os.getcwd()
    filepath = os.path.join(current_dir, filename)
    
    print(f"Attempting to save file to: {filepath}")
    
    try:
        with open(filepath, 'w') as f:
            json.dump(all_resources, f, indent=4)
        print(f"Successfully saved inventory to: {filepath}")
        
        # Debug: List the file
        print("\nDirectory contents after saving:")
        os.system(f"ls -la {os.path.dirname(filepath)}")
    except Exception as e:
        print(f"Error saving file: {e}")
        raise

if __name__ == "__main__":
    main()