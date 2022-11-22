import json
import time
from datetime import datetime
from src.lib.adapters.ssh_adapter import SSHClient
from src.app.constants import HOSTS, SSH_KEYS

def fetch_host_status(ssh, host):
    try:
        if(host not in SSH_KEYS):
            raise Exception(f'Credentials not found for host {host}.')
        response, error = ssh.cmd('cat /proc/loadavg')
        procs, total_procs = response.split()[3].split('/')
        status = 'free' if int(procs) < 7 else 'busy'
        return status
    except:
        raise Exception('Error while fetching host status.')

def process_exists(ssh, process_id):
    response, error = ssh.cmd(f'ps -p {process_id}')
    return str(process_id) in response

def start_simulation(host, simulation):
    try:
        ssh = SSHClient(host, **SSH_KEYS[host]).connect()
        
        # Check if host is free
        print('Checking host status...')
        if(fetch_host_status(ssh, host) == 'busy'):
            ssh.disconnect()
            raise Exception(f'Host {host} is busy.')
        
        print('Host is free.')
        print('Setting up simulation...')
        
        # Create simulation folder
        folder = f'rebound-ctrl/simulations/{simulation["id"]}'
        ssh.cmd(f'mkdir -p {folder}')
        
        # meta.json file content
        meta = {
            'id': simulation['id'], 
            'created_at': simulation['created_at'],
            'inputs': {
                'simulation_type': simulation['simulation_type'],
                'cores': simulation['cores'],
                'integrator': simulation['integrator'],
                'years': simulation['years'],
                'num_logs': simulation['num_logs'],
                'ejection_max_distance': simulation['ejection_max_distance'],
                'particles': simulation['particles'],
            }
        }
        
        if(simulation['simulation_type'] == 'grid'):
            meta['inputs']['grid'] = simulation['grid']
        
        meta_content = json.dumps(meta, indent=4).replace('"', '\\"')
        
        # Upload meta.json file
        ssh.upload(f'src/assets/problem.py', f'{folder}/problem.py')
        
        # Commands to setup simulation folder and start execution
        commands = [
            f'cd {folder}',
            f'echo "{meta_content}" > meta.json',
            f'echo "python -u problem.py" > run.sh',
            f'chmod +x run.sh',
        ]
        print('Starting simulation...')
        ssh.cmd(' && '.join(commands))
        ssh.cmd(f'cd {folder} && nohup ./run.sh > logs.txt 2> errors.txt & echo $! > {folder}/pid.txt', wait_response=False)
        
        try:
            print('Checking simulation status...')
            time.sleep(3)
            process_id = int(ssh.cmd(f'cd {folder} && cat pid.txt')[0])
            if(process_exists(ssh, process_id)):
                print('Simulation started successfully. PID:', process_id)
                ssh.disconnect()
                return True
        except Exception as e:
            print('Error while fetching process id: ', e)
            return False

    except Exception as e:
        print(e)
        return False


# fetch_host_status('ganimedes.rc.unesp.br')

simulation = {
    "id": "aaaaa-bbbbb-cccc-dddd-eeee-ffff",
    "simulation_type": "grid",
    "cores": 16,
    "integrator": "whfast",
    "years": 5.0,
    "num_logs": 50,
    "ejection_max_distance": 20.0,
    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "particles": [
        {
            "m": 1.0
        },
        {
            "m": 1e-3,
            "a": 0.9,
            "e": 0.0
        }
    ],
    "grid": {
        "N": 70,
        "particle": {
            "m": 3e-5,
            "a": [
                0.11,
                1.5
            ],
            "e": [
                0.0,
                0.5
            ]
        }
    }
}
print(start_simulation('ganimedes.rc.unesp.br', simulation))
exit()