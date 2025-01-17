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
                            "Region": region,
                            "InstanceId": instance["InstanceId"],
                            "State": instance["State"]["Name"],
                            "Type": instance["InstanceType"],
                            "PrivateIp": instance.get("PrivateIpAddress"),
                            "PublicIp": instance.get("PublicIpAddress"),
                        }
                        for reservation in instances
                        for instance in reservation["Instances"]
                    ]
                    if ec2_instances:
                        all_resources.setdefault("ec2_instances", []).extend(ec2_instances)

                    # VPCs (Exclude default VPCs)
                    vpcs = client.describe_vpcs().get("Vpcs", [])
                    vpc_list = [
                        {
                            "Region": region,
                            "VpcId": vpc["VpcId"],
                            "CidrBlock": vpc["CidrBlock"],
                            "State": vpc["State"],
                        }
                        for vpc in vpcs
                        if not vpc["IsDefault"]
                    ]
                    if vpc_list:
                        all_resources.setdefault("vpcs", []).extend(vpc_list)

                    # Subnets (Exclude default subnets)
                    subnets = client.describe_subnets().get("Subnets", [])
                    subnet_list = [
                        {
                            "Region": region,
                            "SubnetId": subnet["SubnetId"],
                            "VpcId": subnet["VpcId"],
                            "CidrBlock": subnet["CidrBlock"],
                            "AvailabilityZone": subnet["AvailabilityZone"],
                        }
                        for subnet in subnets
                        if not subnet.get("DefaultForAz", False)
                    ]
                    if subnet_list:
                        all_resources.setdefault("subnets", []).extend(subnet_list)

                    # Security Groups (Exclude default security groups)
                    security_groups = client.describe_security_groups().get("SecurityGroups", [])
                    sg_list = [
                        {
                            "Region": region,
                            "GroupId": sg["GroupId"],
                            "GroupName": sg["GroupName"],
                            "VpcId": sg.get("VpcId", "N/A"),
                            "Description": sg["Description"],
                        }
                        for sg in security_groups
                        if sg["GroupName"] != "default"
                    ]
                    if sg_list:
                        all_resources.setdefault("security_groups", []).extend(sg_list)

                    # Elastic IPs
                    eips = client.describe_addresses().get("Addresses", [])
                    eip_list = [
                        {
                            "Region": region,
                            "PublicIp": eip["PublicIp"],
                            "InstanceId": eip.get("InstanceId", "N/A"),
                            "AllocationId": eip.get("AllocationId", "N/A"),
                        }
                        for eip in eips
                    ]
                    if eip_list:
                        all_resources.setdefault("elastic_ips", []).extend(eip_list)

                elif service == 's3':
                    # S3 Buckets (Global Service)
                    if region == 'us-east-1':  # Only list S3 once since it's global
                        buckets = client.list_buckets()["Buckets"]
                        bucket_list = [{"BucketName": bucket["Name"]} for bucket in buckets]
                        if bucket_list:
                            all_resources.setdefault("s3_buckets", []).extend(bucket_list)

                elif service == 'rds':
                    # RDS Instances
                    rds_instances = client.describe_db_instances().get("DBInstances", [])
                    rds_list = [
                        {
                            "Region": region,
                            "DBInstanceIdentifier": db["DBInstanceIdentifier"],
                            "Engine": db["Engine"],
                            "Status": db["DBInstanceStatus"],
                        }
                        for db in rds_instances
                    ]
                    if rds_list:
                        all_resources.setdefault("rds_instances", []).extend(rds_list)

                elif service == 'lambda':
                    # Lambda Functions
                    functions = client.list_functions().get("Functions", [])
                    lambda_functions = [
                        {
                            "Region": region,
                            "FunctionName": function["FunctionName"],
                            "Runtime": function["Runtime"],
                        }
                        for function in functions
                    ]
                    if lambda_functions:
                        all_resources.setdefault("lambda_functions", []).extend(lambda_functions)

                elif service == 'route53' and region == 'us-east-1':
                    # Route53 Hosted Zones (Global Service)
                    hosted_zones = client.list_hosted_zones().get("HostedZones", [])
                    route53_zones = [{"Id": zone["Id"], "Name": zone["Name"]} for zone in hosted_zones]
                    if route53_zones:
                        all_resources.setdefault("route53_zones", []).extend(route53_zones)

                elif service == 'cloudfront' and region == 'us-east-1':
                    # CloudFront (Global Service)
                    distributions = client.list_distributions().get("DistributionList", {}).get("Items", [])
                    cloudfront_dist = [{"Id": d["Id"], "DomainName": d["DomainName"]} for d in distributions]
                    if cloudfront_dist:
                        all_resources.setdefault("cloudfront_distributions", []).extend(cloudfront_dist)

            except ClientError as e:
                console.print(f"[bold red]Error fetching data for {service} in {region}: {e}[/bold red]")
                continue

    # Print consolidated tables
    for resource_type, items in all_resources.items():
        print_table(resource_type.replace("_", " ").title(), items)

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
