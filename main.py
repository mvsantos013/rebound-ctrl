import paramiko

HOST = 'ganimedes.rc.unesp.br'
USERNAME = 'mateussantos'
PASSWORD = 'MvSantos013'
PORT = 22222

class SSHClient():
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        
    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, username=self.username, password=self.password, port=self.port)
        self.sftp = self.ssh.open_sftp()

    def disconnect(self):
        self.ssh.close()
        self.sftp.close()
    
    def upload(self, local_path, remote_path):
        self.sftp.put(local_path, remote_path)
    
    def download(self, remote_path, local_path):
        self.sftp.get(remote_path, local_path)

if __name__ == '__main__':
    ssh = SSHClient(HOST, USERNAME, PASSWORD, PORT)