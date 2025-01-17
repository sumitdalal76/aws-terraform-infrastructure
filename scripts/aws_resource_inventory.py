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
                    resources = client.describe_instances()
                    instances = [
                        {
                            "InstanceId": instance["InstanceId"],
                            "State": instance["State"]["Name"],
                            "Type": instance["InstanceType"],
                            "PrivateIp": instance.get("PrivateIpAddress"),
                            "PublicIp": instance.get("PublicIpAddress"),
                        }
                        for reservation in resources.get("Reservations", [])
                        for instance in reservation["Instances"]
                    ]
                    print_table("EC2 Instances", instances)
                    all_resources[region]['ec2_instances'] = instances

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
                    resources = client.list_functions()["Functions"]
                    functions = [
                        {
                            "FunctionName": function["FunctionName"],
                            "Runtime": function["Runtime"],
                        }
                        for function in resources
                    ]
                    print_table("Lambda Functions", functions)
                    all_resources[region]['lambda_functions'] = functions

                elif service == 'dynamodb':
                    # DynamoDB Tables
                    resources = client.list_tables()["TableNames"]
                    dynamodb_tables = [{"TableName": table} for table in resources]
                    print_table("DynamoDB Tables", dynamodb_tables)
                    all_resources[region]['dynamodb_tables'] = dynamodb_tables

                elif service == 'elbv2':
                    # Elastic Load Balancers
                    resources = client.describe_load_balancers()["LoadBalancers"]
                    load_balancers = [
                        {
                            "Name": lb["LoadBalancerName"],
                            "DNSName": lb["DNSName"],
                            "Type": lb["Type"],
                        }
                        for lb in resources
                    ]
                    print_table("Load Balancers", load_balancers)
                    all_resources[region]['load_balancers'] = load_balancers

                elif service == 'cloudfront' and region == 'us-east-1':
                    # CloudFront (Global Service)
                    distributions = client.list_distributions()["DistributionList"]["Items"]
                    cloudfront_dist = [{"Id": d["Id"], "DomainName": d["DomainName"]} for d in distributions]
                    print_table("CloudFront Distributions", cloudfront_dist)
                    all_resources[region]['cloudfront_distributions'] = cloudfront_dist

                elif service == 'route53' and region == 'us-east-1':
                    # Route53 (Global Service)
                    hosted_zones = client.list_hosted_zones()["HostedZones"]
                    route53_zones = [{"Id": zone["Id"], "Name": zone["Name"]} for zone in hosted_zones]
                    print_table("Route53 Hosted Zones", route53_zones)
                    all_resources[region]['route53_zones'] = route53_zones

                elif service == 'acm':
                    # ACM Certificates
                    resources = client.list_certificates()["CertificateSummaryList"]
                    certificates = [{"DomainName": cert["DomainName"], "Status": cert["Status"]} for cert in resources]
                    print_table("ACM Certificates", certificates)
                    all_resources[region]['acm_certificates'] = certificates

                elif service == 'sns':
                    # SNS Topics
                    topics = client.list_topics()["Topics"]
                    sns_topics = [{"TopicArn": topic["TopicArn"]} for topic in topics]
                    print_table("SNS Topics", sns_topics)
                    all_resources[region]['sns_topics'] = sns_topics

                elif service == 'sqs':
                    # SQS Queues
                    queues = client.list_queues().get("QueueUrls", [])
                    sqs_queues = [{"QueueUrl": queue} for queue in queues]
                    print_table("SQS Queues", sqs_queues)
                    all_resources[region]['sqs_queues'] = sqs_queues

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
