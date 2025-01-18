# AWS CLI commands for each service
#https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ec2/describe-vpcs.html
AWS_COMMANDS = {
    's3': {
        'command': lambda: ["aws", "s3", "ls"],
        'regional': False,
        'columns': ['Creation Date', 'Time', 'Bucket Name']
    },
    'vpc': {
        'command': lambda region: ["aws", "ec2", "describe-vpcs", "--region", region, "--filters", "Name=is-default,Values=false", "--query", "Vpcs[].[VpcId,Tags[?Key=='Name'].Value|[0],CidrBlock,State,IsDefault,OwnerId]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'VPC ID', 'Name', 'CIDR Block', 'State', 'IsDefault', 'Owner ID']
    },
    'ec2': {
        'command': lambda region: ["aws", "ec2", "describe-instances", "--region", region, "--filters", "Name=instance-state-name,Values=running,stopped", "--query", "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Instance ID', 'Type', 'State']
    },
    'dynamodb': {
        'command': lambda region: ["aws", "dynamodb", "list-tables", "--region", region, "--query", "TableNames[]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Table Name']
    },
    'rds': {
        'command': lambda region: ["aws", "rds", "describe-db-instances", "--region", region, "--output", "text"],
        'regional': True,
        'columns': ['Region', 'DB ID', 'Status']
    },
    'lambda': {
        'command': lambda region: ["aws", "lambda", "list-functions", "--region", region, "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Function Name', 'Runtime']
    },
    'iam': {
        'command': lambda: ["aws", "iam", "list-users", "--query", "Users[].[UserName,CreateDate,PasswordLastUsed]", "--output", "text"],
        'regional': False,
        'columns': ['User Name', 'Created', 'Last Used']
    },
    'cloudfront': {
        'command': lambda: ["aws", "cloudfront", "list-distributions", "--query", "DistributionList.Items[].[Id,DomainName,Enabled,Status]", "--output", "text"],
        'regional': False,
        'columns': ['ID', 'Domain Name', 'Enabled', 'Status']
    },
    'route53': {
        'command': lambda: ["aws", "route53", "list-hosted-zones", "--query", "HostedZones[].[Id,Name,Config.PrivateZone]", "--output", "text"],
        'regional': False,
        'columns': ['Zone ID', 'Domain Name', 'Private']
    },
    'eip': {
        'command': lambda region: ["aws", "ec2", "describe-addresses", "--region", region, "--query", "Addresses[].[PublicIp,InstanceId,Domain]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Public IP', 'Instance ID', 'Domain']
    },
    'elb': {
        'command': lambda region: ["aws", "elbv2", "describe-load-balancers", "--region", region, "--query", "LoadBalancers[].[LoadBalancerName,DNSName,State.Code]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Name', 'DNS Name', 'State']
    }
}