import subprocess
import json
from rich.console import Console
from rich.table import Table
from service_configs import AWS_COMMANDS

console = Console()

def get_service_config(service_name):
    """
    Get configuration for any AWS service
    """
    if service_name not in AWS_COMMANDS:
        raise ValueError(f"Service {service_name} not configured. Please add it to AWS_COMMANDS.")
    
    return {
        'title': f'{service_name.upper()}',
        **AWS_COMMANDS[service_name]
    }

def run_aws_command(command_list):
    """
    Generic function to run AWS CLI commands
    """
    try:
        result = subprocess.run(
            command_list,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"Error running AWS command: {str(e)}")
        return ""

def get_regions():
    """
    Get list of AWS regions
    """
    return run_aws_command([
        "aws", "ec2", "describe-regions",
        "--query", "Regions[].RegionName",
        "--output", "text"
    ]).split()

def scan_service(service_config):
    """
    Generic function to scan AWS services
    """
    try:
        console.print("\n" + "=" * 100)
        console.print(f"# AWS {service_config['title']}")
        console.print("=" * 100 + "\n")
        
        results = []
        
        all_rows = []
        if service_config.get('regional', False):
            for region in get_regions():
                command = service_config['command'](region)
                output = run_aws_command(command)
                if output:
                    for line in output.split('\n'):
                        if line and not line.isspace():
                            values = [region] + [item.strip() for item in line.strip().split('\t')]
                            all_rows.append(values)
        else:
            command = service_config['command']()
            output = run_aws_command(command)
            if output:
                for line in output.split('\n'):
                    if line and not line.isspace():
                        values = [item.strip() for item in line.strip().split()]
                        all_rows.append(values)

        column_widths = [len(col) for col in service_config['columns']]
        for row in all_rows:
            for i, value in enumerate(row):
                if i < len(column_widths):
                    column_widths[i] = max(column_widths[i], len(str(value)))

        column_widths = [width + 2 for width in column_widths]

        header = "| " + " | ".join(f"{col:^{width}}" for col, width in zip(service_config['columns'], column_widths)) + " |"
        separator = "|-" + "-|-".join("-" * width for width in column_widths) + "-|"
        
        console.print(header)
        console.print(separator)
        
        if all_rows:
            for values in all_rows:
                row = "| " + " | ".join(f"{str(v):^{width}}" for v, width in zip(values, column_widths)) + " |"
                console.print(row)
                results.append({'Output': "\t".join(str(v) for v in values)})
        else:
            no_resources = "| No resources found " + " |" * (len(service_config['columns']) - 1)
            console.print(no_resources)
        
        console.print("\n" + "-" * 100)
        
        return results

    except Exception as e:
        console.print(f"Error scanning {service_config['title']}: {str(e)}")
        return []

def scan_aws_resources():
    """
    Main function to scan AWS resources
    """
    all_results = {}
    
    for service in AWS_COMMANDS.keys():
        config = get_service_config(service)
        console.print(f"\nScanning {config['title']}...")
        results = scan_service(config)
        all_results[service] = results
    
    # Save results to file
    with open('aws_inventory.json', 'w') as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    scan_aws_resources()
