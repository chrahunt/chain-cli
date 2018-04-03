import argparse
import logging
import queue
import psutil
import signal
import subprocess
import threading
import time


try:
    import SocketServer as socketserver
except ImportError:
    import socketserver


logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.DEBUG)


class Server(object):
    '''
    TCP server that invokes a callback when any data is received.
    '''
    def __init__(self, address, callback):
        self.server = socketserver.TCPServer(
            address, Server.get_handler(callback))

    def start(self):
        logger.debug('Server.start()')
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = False
        self.thread.start()

    def stop(self):
        if not self.thread: return
        logger.debug('Server.stop()')
        self.server.shutdown()
        self.thread.join()
        self.thread = None

    @staticmethod
    def get_handler(callback):
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                logger.debug('Handler.handle()')
                callback()
        return Handler


class Executor(object):
    def __init__(self, command, callback):
        '''
        Args:
            (str) command the command to run
            (callable) callback the callback to execute on process stop
        '''
        self.command = command
        self.callback = callback

    def start(self):
        logger.debug('Executor.start()')
        self.stopped = False
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = False
        self.thread.start()

    def send_signal(self, signal):
        """
        Send signal to child process.
        """
        logger.debug('Executor.send_signal()')
        try:
            shell = psutil.Process(self.process.pid)
        except psutil.NoSuchProcess:
            return
        for child in shell.children():
            child.send_signal(signal)

    def wait(self):
        if self.stopped: return
        logger.debug('Executor.wait()')
        self.stopped = True
        self.thread.join()
        self.thread = None

    def restart(self):
        self.stopped = True
        self.process.kill()
        self.thread.join()
        self.start()

    def _run(self):
        self.process = subprocess.Popen(self.command, shell=True)
        logger.info('Starting process with pid: {}'.format(self.process.pid))
        self.process.wait()
        if not self.stopped:
            self.stopped = True
            self.callback()


class SortableFunction(object):
    def __init__(self, priority, fn):
        self.priority = priority
        self.fn = fn

    def __call__(self, *args, **kwargs):
        self.fn(*args, **kwargs)

    def __lt__(self, rhs):
        return self.priority < rhs.priority


def signal_test():
    # Test for signal register/handling
    signal.signal(signal.SIGINT, handler)
    while True:
        signal.pause()


def main():
    parser = argparse.ArgumentParser(description='run reloadable command')
    parser.add_argument('command', help='the command to run')
    parser.add_argument('--host', default='localhost', help='the host to listen on')
    parser.add_argument('--port', default=9998, type=int, help='port to listen on')
    parser.add_argument('--restart-method', choices=('term', 'kill'), default='term')
    args = parser.parse_args()

    commands = queue.PriorityQueue()
    # Sources:
    # - tcp server (thread)
    # - command (thread)
    # - signal (none)
    # - keyboard (main)
    def handle_process_stop():
        logger.info('Process has exited.')
        # TODO: listen for keyboard input
    ex = Executor(args.command, handle_process_stop)

    def handle_server_request():
        logger.debug('handle_server_request()')
        def inner():
            logger.info('Restarting process')
            ex.send_signal(signal.SIGINT)
            ex.wait()
            ex.start()
        commands.put(SortableFunction(1, inner))
    server = Server((args.host, args.port), handle_server_request)

    def handle_sigint(*_):
        logger.debug('handle_sigint()')
        def inner():
            ex.send_signal(signal.SIGINT)
            return True
        # Higher priority since we plan to exit.
        commands.put(SortableFunction(0, inner))
    signal.signal(signal.SIGINT, handle_sigint)

    def handle_sigquit(*_):
        logger.debug('handle_sigquit()')
        def inner():
            logger.info('Restarting application')
            ex.send_signal(signal.SIGINT)
            ex.wait()
            ex.start()
        commands.put(SortableFunction(1, inner))
    signal.signal(signal.SIGQUIT, handle_sigquit)

    # Run the command
    ex.start()
    # Start the tcp server
    server.start()
    # Wait for signals or process exit followed by a signal
    while True:
        if commands.get()():
            break

    logger.info('Stopping application')
    server.stop()
    # Additional signals may come at this point and will be directed to the child.
    ex.wait()
