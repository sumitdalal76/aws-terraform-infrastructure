import os
import boto3
from botocore.exceptions import ClientError
import json
from datetime import datetime
from tabulate import tabulate

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
                name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
                instances.append({
                    'Name': name_tag,
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'LaunchTime': instance['LaunchTime'].strftime("%Y-%m-%d %H:%M:%S")
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
                'Identifier': instance['DBInstanceIdentifier'],
                'Engine': f"{instance['Engine']} {instance.get('EngineVersion', 'N/A')}",
                'Size': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus'],
                'Storage': f"{instance.get('AllocatedStorage', 'N/A')} GB"
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
            name_tag = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            vpcs.append({
                'Name': name_tag,
                'VpcId': vpc['VpcId'],
                'CidrBlock': vpc['CidrBlock'],
                'IsDefault': vpc['IsDefault'],
                'State': vpc['State']
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
            # Get bucket location
            location = s3_client.get_bucket_location(Bucket=bucket['Name'])
            region = location['LocationConstraint'] or 'us-east-1'
            
            buckets.append({
                'Name': bucket['Name'],
                'Region': region,
                'CreationDate': bucket['CreationDate'].strftime("%Y-%m-%d %H:%M:%S")
            })
    except ClientError as e:
        print(f"Error getting S3 buckets: {e}")
    return buckets

def create_summary_tables(all_resources):
    """Create summary tables for each resource type"""
    
    # S3 Buckets Summary
    s3_table = tabulate(
        all_resources['S3_Buckets'],
        headers={'Name': 'Bucket Name', 'Region': 'Region', 'CreationDate': 'Created On'},
        tablefmt='grid'
    )
    
    # Regional Resources Summary
    regional_summary = []
    for region in all_resources:
        if region != 'S3_Buckets':
            resources = all_resources[region]
            regional_summary.append({
                'Region': region,
                'EC2 Count': len(resources['EC2_Instances']),
                'RDS Count': len(resources['RDS_Instances']),
                'VPC Count': len(resources['VPCs'])
            })
    
    regional_table = tabulate(
        regional_summary,
        headers={'Region': 'Region', 'EC2 Count': 'EC2', 'RDS Count': 'RDS', 'VPC Count': 'VPCs'},
        tablefmt='grid'
    )
    
    return s3_table, regional_table

def main():
    print("\n=== AWS Resource Inventory ===\n")
    
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
    
    # Create summary tables
    s3_table, regional_table = create_summary_tables(all_resources)
    
    # Print summary tables
    print("\n=== S3 Buckets ===")
    print(s3_table)
    print("\n=== Regional Resource Summary ===")
    print(regional_table)
    
    # Save detailed results to a JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aws_resources_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(all_resources, f, indent=4)
        print(f"\nDetailed inventory has been saved to: {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")
        raise

if __name__ == "__main__":
    main()