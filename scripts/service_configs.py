#For commands refer to the following links:
#https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ec2/describe-vpcs.html


# AWS CLI commands for each service
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
    'subnet': {
        'command': lambda region: ["aws", "ec2", "describe-subnets", "--region", region, "--filters", "Name=default-for-az,Values=false", "--query", "Subnets[].[SubnetId,Tags[?Key=='Name'].Value|[0],VpcId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Subnet ID', 'Name', 'VPC ID', 'CIDR Block', 'AZ', 'Auto-assign Public IP']
    },
    'security-group': {
        'command': lambda region: ["aws", "ec2", "describe-security-groups", "--region", region, "--filters", "Name=group-name,Values=!default", "--query", "SecurityGroups[].[GroupId,GroupName,VpcId,Description]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Security Group ID', 'Name', 'VPC ID', 'Description']
    },
    'route-table': {
        'command': lambda region: ["aws", "ec2", "describe-route-tables", "--region", region, "--filters", "Name=association.main,Values=false", "--query", "RouteTables[].[RouteTableId,Tags[?Key=='Name'].Value|[0],VpcId]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Route Table ID', 'Name', 'VPC ID']
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
    'iam-user': {
        'command': lambda: ["aws", "iam", "list-users", "--query", "Users[].[UserName,CreateDate,PasswordLastUsed]", "--output", "text"],
        'regional': False,
        'columns': ['User Name', 'Created', 'Last Used']
    },
    'iam-role': {
        'command': lambda: ["aws", "iam", "list-roles", "--query", "Roles[].[RoleName,CreateDate,Arn]", "--output", "text"],
        'regional': False,
        'columns': ['Role Name', 'Created', 'ARN']
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
    },
    'ecs': {
        'command': lambda region: ["aws", "ecs", "list-clusters", "--query", "clusterArns[]", "--region", region, "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Cluster ARN']
    },
    'eks': {
        'command': lambda region: ["aws", "eks", "list-clusters", "--region", region, "--query", "clusters[]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Cluster Name']
    },
    'sns': {
        'command': lambda region: ["aws", "sns", "list-topics", "--region", region, "--query", "Topics[].[TopicArn]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Topic ARN']
    },
    'sqs': {
        'command': lambda region: ["aws", "sqs", "list-queues", "--region", region, "--query", "QueueUrls[]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Queue URL']
    },
    'ecr': {
        'command': lambda region: ["aws", "ecr", "describe-repositories", "--region", region, "--query", "repositories[].[repositoryName,repositoryUri]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Repository Name', 'Repository URI']
    },
    'acm': {
        'command': lambda region: ["aws", "acm", "list-certificates", "--region", region, "--query", "CertificateSummaryList[].[CertificateArn,DomainName,Status]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Certificate ARN', 'Domain Name', 'Status']
    },
    'cloudwatch': {
        'command': lambda region: ["aws", "cloudwatch", "list-metrics", "--region", region, "--query", "Metrics[].[Namespace,MetricName]", "--output", "text"],
        'regional': True,
        'columns': ['Region', 'Namespace', 'Metric Name']
    }
}