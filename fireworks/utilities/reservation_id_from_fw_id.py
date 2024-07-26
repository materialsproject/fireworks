import os
import subprocess
import re
import json
import sys
import getpass
import paramiko

# ANSI color codes for terminal output
RED = '\033[0;31m'
CYAN = '\033[0;36m'
ORANGE = '\033[0;33m'
NC = '\033[0m'  # No Color

def run_command(command, ssh=None):
    if ssh:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        errors = stderr.read().decode('utf-8').strip()
        if errors:
            raise Exception(f"Command failed: {command}\n{errors}")
        return output
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            #raise Exception(f"Command failed: {command}\n{result.stderr}")
            raise Exception('Running locally')
        return result.stdout.strip()

def execute_command(command):
    try:
        return run_command(command), None
    except Exception as e:
        print(e)
        return ssh_login(command)

def extract_username_hostname(input_string):
    pattern = r'(?P<username>[^@]+)@(?P<hostname>.+)'
    match = re.match(pattern, input_string)
    if match:
        return match.group('username'), match.group('hostname')
    else:
        raise ValueError("The input does not match the required format 'username@hostname'.")

def ssh_login(command):
    input_string = input("Enter username@hostname: ").strip()
    username, hostname = extract_username_hostname(input_string)
    password = getpass.getpass('Enter password+OTP: ')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    
    return run_command(command, ssh), ssh

def get_stdout_dir(job_id, ssh=None):
    command = f"scontrol show jobid {job_id}"
    output = run_command(command, ssh)
    match = re.search(r"StdOut=(\S+)", output)
    if match:
        return match.group(1)
    else:
        print(f"{RED}StdOut path not found in job information{NC}")
        sys.exit(1)

def load_json(file_path, ssh=None):
    if ssh:
        command = f"cat {file_path}"
        json_data = run_command(command, ssh)
        return json.loads(json_data)
    else:
        with open(file_path) as f:
            return json.load(f)

def process_all_jobs(job_list,ssh=None):
    fw_dict = {}
    #user = os.getenv('USER')
    #job_list = run_command(f"squeue --states=R -u {user}", ssh)
    job_lines = job_list.splitlines()[1:]  # Skip header
    if not job_lines:
        print(f"{RED}No jobs found!{NC}")
        sys.exit(1)
    load_length=len(job_lines)
    for i,line in enumerate(job_lines):
        i=i+1
        job_id = line.split()[0]
        percent_complete = (i / load_length) * 100
        
        # Create the bar part of the output
        bar = '#' * i + '-' * (load_length - i)
        
        # Display the loading bar along with the percentage
        sys.stdout.write(f'\r[{bar}] {percent_complete:.2f}%')
        sys.stdout.flush()
        print("\n")
        #print(f"{ORANGE}Processing job ID: {CYAN}{job_id}{NC}")
        fw_id = process_single_job(job_id, ssh)
        fw_dict[fw_id] = job_id


    return fw_dict

def process_single_job(job_id, ssh=None):
    stdout_dir = get_stdout_dir(job_id, ssh)
    base_dir = os.path.dirname(stdout_dir)
    return dir_rapidfire(base_dir, ssh)

def dir_singleshot(base_dir, ssh=None):
    json_file = os.path.join(base_dir, "FW.json")
    if ssh:
        command = f"test -f {json_file} && cat {json_file}"
        try:
            data = run_command(command, ssh)
            data = json.loads(data)
        except:
            print_warning(base_dir)
            return 1
    else:
        if os.path.isfile(json_file):
            data = load_json(json_file)
        else:
            print_warning(base_dir)
            return 1

    spec_mpid = data.get('spec', {}).get('MPID')
    fw_id = data.get('fw_id')
    if spec_mpid:
        print(f"spec.MPID: {spec_mpid}")
    if fw_id:
        print(f"fw_id: {fw_id}")
    return fw_id if fw_id else 1

def dir_rapidfire(base_dir, ssh=None):
    if ssh:
        command = f"cd {base_dir} && ls -d launcher_*"
        try:
            launcher_dirs = run_command(command, ssh).split()
        except:
            return dir_singleshot(base_dir, ssh)
    else:
        launcher_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("launcher_")]

    if not launcher_dirs:
        return dir_singleshot(base_dir, ssh)

    largest_dir = sorted(launcher_dirs, reverse=True)[0]
    launcher_path = os.path.join(base_dir, largest_dir)
    json_file = os.path.join(launcher_path, "FW.json")

    if ssh:
        command = f"test -f {json_file} && cat {json_file}"
        try:
            data = run_command(command, ssh)
            data = json.loads(data)
        except:
            print_warning(base_dir)
            return dir_singleshot(base_dir, ssh)
    else:
        if os.path.isfile(json_file):
            data = load_json(json_file)
        else:
            print_warning(base_dir)
            return dir_singleshot(base_dir)

    spec_mpid = data.get('spec', {}).get('MPID')
    fw_id = data.get('fw_id')
    #print(f"spec.MPID: {spec_mpid}")
    #print(f"fw_id: {fw_id}")
    return fw_id

def print_warning(dir_path):
    warning_message = f"""
    {"-" * 77}
    |                                                                             |
    |           W    W    AA    RRRRR   N    N  II  N    N   GGGG   !!!           |
    |           W    W   A  A   R    R  NN   N  II  NN   N  G    G  !!!           |
    |           W    W  A    A  R    R  N N  N  II  N N  N  G       !!!           |
    |           W WW W  AAAAAA  RRRRR   N  N N  II  N  N N  G  GGG   !            |
    |           WW  WW  A    A  R   R   N   NN  II  N   NN  G    G                |
    |           W    W  A    A  R    R  N    N  II  N    N   GGGG   !!!           |
    |                                                                             |
    |     This slurm job probably doesn't have an FW_ID associated with it.       |
    |     something probably went wrong. You can probably check the directory     |
    |     above to maybe figure out what happened. Best of luck                   |
    |                    Also why are you using singleshot                        |
    |                                                                             |
    {"-" * 77}
    """
    print(warning_message)

def main(fw_id):
    current_dir = os.getcwd()
    fw_dict = {}

    command = "squeue --states=R -u ${USER}"
    result, ssh = execute_command(command)
    #print(result)

    fw_dict = process_all_jobs(result,ssh)

    os.chdir(current_dir)
    jobid=fw_dict.get(fw_id)
    return jobid

#if __name__ == "__main__":
 #   main()
