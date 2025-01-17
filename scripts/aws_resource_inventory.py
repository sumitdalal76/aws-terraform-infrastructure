#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
import json

# Initialize console for table output
console = Console()

def list_all_resources():
    session = boto3.Session()
    ec2_client = session.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # Supported services
    services = [
        'ec2', 's3', 'rds', 'lambda', 'dynamodb', 'elbv2', 'cloudfront', 'route53', 
        'acm', 'sns', 'sqs', 'eks', 'ecr', 'cloudwatch'
    ]

    all_resources = {}

    for region in regions:
        console.print(f"[bold cyan]Scanning region: {region}[/bold cyan]")
        all_resources[region] = {}

        for service in services:
            try:
                client = session.client(service, region_name=region)
                console.print(f"[bold green]Service: {service}[/bold green]")

                if service == 'ec2':
                    # EC2 Instances
                    instances = client.describe_instances().get("Reservations", [])
                    ec2_instances = [
                        {
                            "InstanceId": instance["InstanceId"],
                            "State": instance["State"]["Name"],
                            "Type": instance["InstanceType"],
                            "PrivateIp": instance.get("PrivateIpAddress"),
                            "PublicIp": instance.get("PublicIpAddress"),
                        }
                        for reservation in instances
                        for instance in reservation["Instances"]
                    ]
                    print_table("EC2 Instances", ec2_instances)
                    all_resources[region]['ec2_instances'] = ec2_instances

                    # VPCs
                    vpcs = client.describe_vpcs().get("Vpcs", [])
                    vpc_list = [
                        {
                            "VpcId": vpc["VpcId"],
                            "CidrBlock": vpc["CidrBlock"],
                            "State": vpc["State"],
                            "IsDefault": vpc["IsDefault"],
                        }
                        for vpc in vpcs
                    ]
                    print_table("VPCs", vpc_list)
                    all_resources[region]['vpcs'] = vpc_list

                    # Subnets
                    subnets = client.describe_subnets().get("Subnets", [])
                    subnet_list = [
                        {
                            "SubnetId": subnet["SubnetId"],
                            "VpcId": subnet["VpcId"],
                            "CidrBlock": subnet["CidrBlock"],
                            "AvailabilityZone": subnet["AvailabilityZone"],
                        }
                        for subnet in subnets
                    ]
                    print_table("Subnets", subnet_list)
                    all_resources[region]['subnets'] = subnet_list

                    # Security Groups
                    security_groups = client.describe_security_groups().get("SecurityGroups", [])
                    sg_list = [
                        {
                            "GroupId": sg["GroupId"],
                            "GroupName": sg["GroupName"],
                            "VpcId": sg.get("VpcId", "N/A"),
                            "Description": sg["Description"],
                        }
                        for sg in security_groups
                    ]
                    print_table("Security Groups", sg_list)
                    all_resources[region]['security_groups'] = sg_list

                    # Elastic IPs
                    eips = client.describe_addresses().get("Addresses", [])
                    eip_list = [
                        {
                            "PublicIp": eip["PublicIp"],
                            "InstanceId": eip.get("InstanceId", "N/A"),
                            "AllocationId": eip.get("AllocationId", "N/A"),
                        }
                        for eip in eips
                    ]
                    print_table("Elastic IPs", eip_list)
                    all_resources[region]['elastic_ips'] = eip_list

                elif service == 's3':
                    # S3 Buckets (Global Service)
                    if region == 'us-east-1':  # Only list S3 once since it's global
                        buckets = client.list_buckets()["Buckets"]
                        bucket_list = [{"BucketName": bucket["Name"]} for bucket in buckets]
                        print_table("S3 Buckets", bucket_list)
                        all_resources[region]['s3_buckets'] = bucket_list

                elif service == 'rds':
                    # RDS Instances
                    resources = client.describe_db_instances()["DBInstances"]
                    rds_instances = [
                        {
                            "DBInstanceIdentifier": db["DBInstanceIdentifier"],
                            "Engine": db["Engine"],
                            "Status": db["DBInstanceStatus"],
                        }
                        for db in resources
                    ]
                    print_table("RDS Instances", rds_instances)
                    all_resources[region]['rds_instances'] = rds_instances

                elif service == 'lambda':
                    # Lambda Functions
                    functions = client.list_functions()["Functions"]
                    lambda_functions = [
                        {
                            "FunctionName": function["FunctionName"],
                            "Runtime": function["Runtime"],
                        }
                        for function in functions
                    ]
                    print_table("Lambda Functions", lambda_functions)
                    all_resources[region]['lambda_functions'] = lambda_functions

                elif service == 'route53' and region == 'us-east-1':
                    # Route53 Hosted Zones (Global Service)
                    zones = client.list_hosted_zones().get("HostedZones", [])
                    route53_zones = [{"Id": zone["Id"], "Name": zone["Name"]} for zone in zones]
                    print_table("Route53 Hosted Zones", route53_zones)
                    all_resources[region]['route53_zones'] = route53_zones

                elif service == 'cloudfront' and region == 'us-east-1':
                    # CloudFront (Global Service)
                    distributions = client.list_distributions()
                    distribution_list = distributions.get("DistributionList", {})
                    items = distribution_list.get("Items", [])
                    cloudfront_dist = [{"Id": d["Id"], "DomainName": d["DomainName"]} for d in items]
                    print_table("CloudFront Distributions", cloudfront_dist)
                    all_resources[region]['cloudfront_distributions'] = cloudfront_dist

            except ClientError as e:
                console.print(f"[bold red]Error fetching data for {service} in {region}: {e}[/bold red]")
                continue

    # Save inventory to JSON
    with open("aws_all_resources.json", "w") as f:
        json.dump(all_resources, f, indent=4)
    console.print("[bold cyan]Inventory saved to aws_all_resources.json[/bold cyan]")

def print_table(title, items):
    """Prints a table with a dynamic column structure."""
    if not items:
        console.print(f"[bold yellow]{title}: No resources found.[/bold yellow]")
        return

    table = Table(title=title)
    keys = items[0].keys()  # Extract keys from the first item
    for key in keys:
        table.add_column(key)

    for item in items:
        table.add_row(*[str(item[key]) for key in keys])

    console.print(table)

if __name__ == "__main__":
    list_all_resources()
