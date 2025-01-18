import os
import json
import subprocess
from rich.console import Console
from rich.table import Table

# Initialize console for better terminal output
console = Console()

def run_aws_list_all():
    """
    Run the aws-list-all command to scan only S3 resources.
    """
    output_dir = "aws_list_all_output"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    console.print("[bold cyan]Running aws-list-all for S3 buckets...[/bold cyan]")

    try:
        # First, verify AWS credentials are working
        verify_cmd = subprocess.run(
            ["aws", "s3", "ls"],
            check=True,
            capture_output=True,
            text=True
        )
        console.print(f"[bold green]AWS Credentials check:[/bold green]\n{verify_cmd.stdout}")

        # Run aws-list-all with correct parameters
        console.print("[bold yellow]Running aws-list-all command...[/bold yellow]")
        result = subprocess.run(
            [
                "aws-list-all",
                "list",
                "--service=s3",
                "--output-dir", output_dir,
                "--debug"
            ],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, 'AWS_DEFAULT_OUTPUT': 'json'}
        )
        
        if result.stdout:
            console.print(f"[bold green]Command output:[/bold green]\n{result.stdout}")
        if result.stderr:
            console.print(f"[bold yellow]Debug output:[/bold yellow]\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error running command: {e.cmd}[/bold red]")
        if hasattr(e, 'output') and e.output:
            console.print(f"[bold red]Command output: {e.output}[/bold red]")
        if hasattr(e, 'stderr') and e.stderr:
            console.print(f"[bold red]Error output: {e.stderr}[/bold red]")
        
        # Fallback to direct AWS CLI
        try:
            console.print("[bold yellow]Attempting to list buckets with AWS CLI as fallback...[/bold yellow]")
            aws_s3_ls = subprocess.run(
                ["aws", "s3", "ls", "--output", "json"],
                check=True,
                capture_output=True,
                text=True
            )
            console.print(f"[bold green]AWS S3 buckets:[/bold green]\n{aws_s3_ls.stdout}")
        except subprocess.CalledProcessError as aws_error:
            console.print(f"[bold red]Error listing buckets with AWS CLI: {aws_error}[/bold red]")
        raise

    return output_dir

def parse_and_display(output_dir):
    """
    Parse the JSON files generated by aws-list-all and display the results in a table.
    """
    all_resources = []

    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                console.print(f"[bold blue]Processing file: {file_path}[/bold blue]")
                
                with open(file_path, "r") as f:
                    try:
                        # Parse JSON data
                        data = json.load(f)
                        console.print(f"[bold green]File contents:[/bold green]\n{json.dumps(data, indent=2)}")
                        
                        service = data.get("Service", "Unknown")
                        operation = data.get("Operation", "Unknown")

                        # Look for Buckets in the response
                        if "Buckets" in data.get("Resources", {}):
                            buckets = data["Resources"]["Buckets"]
                            for bucket in buckets:
                                all_resources.append({
                                    "Service": service,
                                    "Operation": operation,
                                    "Resource": bucket,
                                })
                        
                    except json.JSONDecodeError as e:
                        console.print(f"[bold red]Error parsing JSON file {file_path}: {e}[/bold red]")

    if all_resources:
        print_resources_table(all_resources)
        save_to_json(all_resources, "aws_s3_resources_summary.json")
    else:
        console.print("[bold yellow]No S3 buckets found. Please verify your AWS credentials and permissions.[/bold yellow]")

def print_resources_table(resources):
    """
    Print the resources in a table format.
    """
    table = Table(title="AWS S3 Resources")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Operation", style="green")
    table.add_column("Resource", style="magenta")

    for resource in resources:
        table.add_row(
            resource["Service"],
            resource["Operation"],
            resource["Resource"]
        )

    console.print(table)

def save_to_json(data, filename):
    """
    Save the resource data to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    console.print(f"[bold green]Resource data saved to {filename}[/bold green]")

if __name__ == "__main__":
    output_dir = run_aws_list_all()
    parse_and_display(output_dir)
