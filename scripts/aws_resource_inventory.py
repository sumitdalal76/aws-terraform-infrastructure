import subprocess
from rich.console import Console
from rich.table import Table

# Initialize console for better terminal output
console = Console()

def list_s3_buckets():
    """
    List S3 buckets using AWS CLI
    """
    try:
        # List buckets using AWS CLI
        result = subprocess.run(
            ["aws", "s3", "ls"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create and populate table
        table = Table(title="AWS S3 Buckets")
        table.add_column("Creation Date", style="cyan")
        table.add_column("Bucket Name", style="green")
        
        # Parse and add each bucket to the table
        for line in result.stdout.strip().split('\n'):
            if line:  # Skip empty lines
                date_str, bucket_name = line.strip().split(' ', 1)
                table.add_row(date_str, bucket_name)
        
        # Print the table
        console.print(table)

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error listing buckets: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    list_s3_buckets()
