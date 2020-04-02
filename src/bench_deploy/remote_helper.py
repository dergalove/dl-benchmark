import abc
import paramiko
import wmi

class remote_helper(metaclass = abc.ABCMeta):
    def __init__(self, log):
        self.my_log = log

    @staticmethod
    def get_remote_helper(os_type, log):
        if os_type == 'linux':
            return linux_remote_helper(log)
        elif os_type == 'windows':
            return windows_remote_hepler(log)

    @abc.abstractmethod
    def connect(self, machine_ip, login, password):
        pass

    @abc.abstractmethod
    def execute(self, con, command):
        pass

    @abc.abstractmethod
    def wait(self, process):
        pass

class linux_remote_helper(remote_helper):
    def __init__(self, log):
        super().__init__(log)

    def connect(self, machine_ip, login, password):
        new_connection = paramiko.SSHClient()
        new_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        new_connection.connect(hostname = machine_ip, username = login,
            password = password)

        return new_connection

    def execute(self, con, command):
        transport = con.get_transport()
        channel = transport.open_session()

        try:
            channel.exec_command(command)
            self.my_log.info('Process started successfully')
        except paramiko.ssh_exception.SSHException:
            raise RuntimeError('Failed to create process!')

        return channel

    def wait(self, process):
        channel_id = process.get_id()
        process_status = process.recv_exit_status()
        self.my_log.info('Process ended on Linux with id {}'.format(channel_id))

class windows_remote_hepler(remote_helper):
    def __init__(self, log):
        super().__init__(log)

    def connect(self, machine_ip, login, password):
        new_connection = wmi.WMI(machine_ip, user = login,
            password = password)

        return new_connection

    def execute(self, con, command):
        process_startup = con.Win32_ProcessStartup.new()
        process_id, result = con.Win32_Process.Create(CommandLine = command,
            ProcessStartupInformation = process_startup)

        watcher = None
        if result == 0:
            self.my_log.info('Process started successfully {}'.format(process_id))
            con.watch_for(notification_type = 'Deletion',
                wmi_class = 'Win32_Process', ProcessId = process_id)
        else:
            raise RuntimeError('Failed to create process!')

        return watcher

    def wait(self, process):
        process_status = process()
        self.my_log.info('Process ended on Windows with name {}'.format(
            process_status.CSName))
