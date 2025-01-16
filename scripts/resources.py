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

def get_lambda_functions(region):
    """Get Lambda functions in the region"""
    lambda_client = boto3.client('lambda', region_name=region)
    functions = []
    try:
        response = lambda_client.list_functions()
        for function in response.get('Functions', []):
            functions.append({
                'Name': function['FunctionName'],
                'Runtime': function['Runtime'],
                'Memory': f"{function['MemorySize']} MB",
                'Timeout': f"{function['Timeout']} sec",
                'LastModified': function['LastModified']
            })
    except ClientError as e:
        print(f"Error getting Lambda functions in {region}: {e}")
    return functions

def get_dynamodb_tables(region):
    """Get DynamoDB tables in the region"""
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    tables = []
    try:
        response = dynamodb_client.list_tables()
        for table_name in response.get('TableNames', []):
            table_info = dynamodb_client.describe_table(TableName=table_name)['Table']
            tables.append({
                'Name': table_name,
                'Status': table_info['TableStatus'],
                'Size': table_info.get('TableSizeBytes', 'N/A'),
                'ItemCount': table_info.get('ItemCount', 0)
            })
    except ClientError as e:
        print(f"Error getting DynamoDB tables in {region}: {e}")
    return tables

def get_elasticache_clusters(region):
    """Get ElastiCache clusters in the region"""
    elasticache_client = boto3.client('elasticache', region_name=region)
    clusters = []
    try:
        response = elasticache_client.describe_cache_clusters()
        for cluster in response.get('CacheClusters', []):
            clusters.append({
                'Id': cluster['CacheClusterId'],
                'Engine': f"{cluster['Engine']} {cluster.get('EngineVersion', 'N/A')}",
                'Type': cluster['CacheNodeType'],
                'Status': cluster['CacheClusterStatus']
            })
    except ClientError as e:
        print(f"Error getting ElastiCache clusters in {region}: {e}")
    return clusters

def get_api_gateways(region):
    """Get API Gateway APIs in the region"""
    apigw_client = boto3.client('apigateway', region_name=region)
    apis = []
    try:
        response = apigw_client.get_rest_apis()
        for api in response.get('items', []):
            apis.append({
                'Name': api['name'],
                'Id': api['id'],
                'Description': api.get('description', 'N/A'),
                'CreatedDate': api['createdDate'].strftime("%Y-%m-%d %H:%M:%S")
            })
    except ClientError as e:
        print(f"Error getting API Gateways in {region}: {e}")
    return apis

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
                'EC2': len(resources['EC2_Instances']),
                'RDS': len(resources['RDS_Instances']),
                'VPCs': len(resources['VPCs']),
                'Lambda': len(resources['Lambda_Functions']),
                'DynamoDB': len(resources['DynamoDB_Tables']),
                'ElastiCache': len(resources['ElastiCache_Clusters']),
                'API_Gateway': len(resources['API_Gateways'])
            })
    
    regional_table = tabulate(
        regional_summary,
        headers={
            'Region': 'Region',
            'EC2': 'EC2',
            'RDS': 'RDS',
            'VPCs': 'VPCs',
            'Lambda': 'λ',
            'DynamoDB': 'DDB',
            'ElastiCache': 'Cache',
            'API_Gateway': 'API GW'
        },
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
            'VPCs': get_vpcs(region),
            'Lambda_Functions': get_lambda_functions(region),
            'DynamoDB_Tables': get_dynamodb_tables(region),
            'ElastiCache_Clusters': get_elasticache_clusters(region),
            'API_Gateways': get_api_gateways(region)
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