import io
import paramiko

class SSHClient():
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.sftp = None
        
    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.host, username=self.username, password=self.password, port=self.port)
        except Exception as e:
            if('timed out' in str(e).lower()):
                raise Exception(f'{self.host} connection timeout.')
            raise Exception(f'{self.host} SSH connection error: {e}')
        return self

    def disconnect(self):
        self.ssh.close()
        if(self.sftp):
            self.sftp.close()
    
    def upload(self, local_path, remote_path):
        if(not self.sftp):
            self.sftp = self.ssh.open_sftp()
        self.sftp.put(local_path, remote_path)
    
    def download(self, remote_path):
        if(not self.sftp):
            self.sftp = self.ssh.open_sftp()
        buffer = io.BytesIO()
        self.sftp.getfo(remote_path, buffer)
        buffer.seek(0)
        return buffer
    
    def cmd(self, command, wait_response=True):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        if(wait_response):
            return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')
        return True