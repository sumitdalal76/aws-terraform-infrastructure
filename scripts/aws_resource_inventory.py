#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from rich.console import Console
from rich.table import Table
import json
import os
from concurrent.futures import ThreadPoolExecutor

# Initialize console for pretty output
console = Console()

# Directory to save the output files
OUTPUT_DIR = "./aws_resources"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_regions():
    """Retrieve all AWS regions."""
    ec2 = boto3.client("ec2")
    return [region["RegionName"] for region in ec2.describe_regions()["Regions"]]


def get_services():
    """Retrieve all available AWS services."""
    session = boto3.Session()
    return session.get_available_services()


def list_resources_for_service(client, service, region):
    """List all resources for a given service and region."""
    operations = client.meta.service_model.operation_names
    list_operations = [op for op in operations if op.startswith("list_") or op.startswith("describe_")]
    results = {}

    for operation in list_operations:
        try:
            # Call the operation dynamically
            method = getattr(client, operation)
            paginator = client.get_paginator(operation)
            response_iterator = paginator.paginate()

            # Collect all results
            resources = []
            for page in response_iterator:
                for key, value in page.items():
                    if isinstance(value, list):
                        resources.extend(value)

            if resources:
                results[operation] = resources

        except ClientError as e:
            console.print(f"[bold yellow]Permission issue for {operation} in {service}: {e}[/bold yellow]")
        except EndpointConnectionError as e:
            console.print(f"[bold red]Connection issue for {operation} in {service}: {e}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Error for {operation} in {service}: {e}[/bold red]")

    return results


def scan_region(region, services):
    """Scan all resources for all services in a region."""
    session = boto3.Session(region_name=region)
    region_resources = {}

    for service in services:
        try:
            client = session.client(service)
            console.print(f"[bold green]Scanning {service} in {region}[/bold green]")
            resources = list_resources_for_service(client, service, region)

            if resources:
                region_resources[service] = resources

        except Exception as e:
            console.print(f"[bold red]Failed to initialize client for {service} in {region}: {e}[/bold red]")

    return region_resources


def main():
    console.print("[bold cyan]Starting AWS Resource Inventory...[/bold cyan]")

    regions = get_regions()
    services = get_services()

    console.print(f"[bold cyan]Scanning resources for all regions: {', '.join(regions)}[/bold cyan]")
    console.print(f"[bold cyan]Scanning for all services: {', '.join(services)}[/bold cyan]")

    all_resources = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_region, region, services): region for region in regions}

        for future in futures:
            region = futures[future]
            try:
                region_resources = future.result()
                if region_resources:
                    all_resources[region] = region_resources

                    # Save each region's resources to a file
                    with open(f"{OUTPUT_DIR}/{region}_resources.json", "w") as f:
                        json.dump(region_resources, f, indent=4)

            except Exception as e:
                console.print(f"[bold red]Error processing region {region}: {e}[/bold red]")

    # Save all resources to a consolidated file
    with open(f"{OUTPUT_DIR}/all_resources.json", "w") as f:
        json.dump(all_resources, f, indent=4)

    console.print(f"[bold green]All resources saved to {OUTPUT_DIR}/all_resources.json[/bold green]")


if __name__ == "__main__":
    main()
