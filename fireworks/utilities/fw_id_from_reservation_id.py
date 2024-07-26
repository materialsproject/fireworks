import os
import subprocess
import json
import paramiko
import getpass
import re

# Function to execute local shell commands and return the output
def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            #raise Exception(f"Command failed: {command}\n{result.stderr}")
            raise Exception('Running fireworks locally')
        ssh=None
        return result.stdout.strip(),ssh
    except Exception as e:
        result,ssh=ssh_login(command)
        print(e)
        return result,ssh


def extract_username_hostname(input_string):
    # Define the regex pattern
    pattern = r'(?P<username>[^@]+)@(?P<hostname>.+)'

    # Search for the pattern in the input string
    match = re.match(pattern, input_string)

    if match:
        # Extract username and hostname from named groups
        username = match.group('username')
        hostname = match.group('hostname')
        return username, hostname
    else:
        raise ValueError("The input does not match the required format 'username@hostname'.")

# Get user input

# SSH login and execute remote command
def ssh_login(command):
    input_string = input("Enter username@hostname: ").strip()
    username, hostname = extract_username_hostname(input_string)
    password = getpass.getpass('Enter password+OTP: ')

    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the server
        ssh.connect(hostname, username=username, password=password)
        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        errors = stderr.read().decode('utf-8').strip()

        if errors:
            raise Exception(f"Command failed: {command}\n{errors}")
       
    except Exception as e:
        print(e)
    return output, ssh
        

def get_fwid(jobid):
    job_info,ssh = execute_command(f"scontrol show jobid {jobid}")
    if ssh !=None:
        fw_id=find_worker(job_info,ssh)
        ssh.close()
    else:
        fw_id=find_worker(job_info,ssh)

    return fw_id


def find_worker(job_info, ssh):
    stdout_dir = ""
    for line in job_info.splitlines():
        if "StdOut=" in line:
            stdout_dir = line.split("=", 1)[1]
            break
    
    if not stdout_dir:
        print("StdOut path not found in job information")
        return

    base_dir = os.path.dirname(stdout_dir)

    if ssh!=None:
        # Change directory to the base directory on the remote server
        stdin, stdout, stderr = ssh.exec_command(f"cd {base_dir} && pwd")
        current_dir = stdout.read().decode('utf-8').strip()
        errors = stderr.read().decode('utf-8').strip()
        if errors:
            raise Exception(f"Failed to change directory: {errors}")
        
        print(f"Changed directory to: {current_dir}")

        stdin, stdout, stderr = ssh.exec_command(f"find {current_dir} -type d -name 'launcher_*'")
        launch_dirs = stdout.read().decode('utf-8').splitlines()
        errors = stderr.read().decode('utf-8').strip()
        if errors:
            raise Exception(f"Failed to find launch directories: {errors}")

        largest_dir = max(launch_dirs, key=lambda d: d.split('_')[-1])

        # Change to the largest directory
        stdin, stdout, stderr = ssh.exec_command(f"cd {largest_dir} && pwd")
        final_dir = stdout.read().decode('utf-8').strip()
        errors = stderr.read().decode('utf-8').strip()
        if errors:
            raise Exception(f"Failed to change directory to {largest_dir}: {errors}")

        print(f"Changed directory to: {final_dir}")

        # Check for the JSON file in the directory
        stdin, stdout, stderr = ssh.exec_command(f"cat {final_dir}/FW.json")
        json_data = stdout.read().decode('utf-8').strip()
        errors = stderr.read().decode('utf-8').strip()
        if errors:
            raise Exception(f"Failed to read FW.json: {errors}")

        data = json.loads(json_data)
        spec_mpid = data.get('spec', {}).get('MPID', 'N/A')
        fw_id = data.get('fw_id', 'N/A')

        print(f"spec.MPID: {spec_mpid}")
        print(f"fw_id: {fw_id}")
    else:
        # Change directory to the extracted base directory
        try:
            os.chdir(base_dir)
        except OSError:
            print(f"Failed to change directory to {base_dir}")
            exit(1)

        # Print the current directory to confirm
        print(f"Changed directory to: {os.getcwd()}")

        # Find the largest directory with the pattern "launcher_*"
        launch_dirs = subprocess.check_output(f"find {os.getcwd()} -type d -name 'launcher_*'", shell=True).decode().splitlines()
        largest_dir = max(launch_dirs, key=lambda d: d.split('_')[-1])

        try:
            os.chdir(largest_dir)
        except OSError:
            print(f"Failed to change directory to {largest_dir}")
            exit(1)

        print(f"Changed directory to: {os.getcwd()}")

        json_file = os.path.join(os.getcwd(), "FW.json")

        # Check if the JSON file exists
        if os.path.isfile(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            spec_mpid = data.get('spec', {}).get('MPID', 'N/A')
            fw_id = data.get('fw_id', 'N/A')

            # Output the extracted values
            print(f"spec.MPID: {spec_mpid}")
            print(f"fw_id: {fw_id}")
        else:
            print(f"FW.json not found in {largest_dir}")
            
            return fw_id
    return fw_id