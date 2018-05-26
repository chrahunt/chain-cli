# command-restarter

Reload/refresh commands as part of a development workflow.

## Usage

Use another command-line tool or script to watch for changes to files.

```
crestart 'docker-compose up'
```

Then in any other watch or command-execution scripts I can force the command
to reload using a tcp request to the default endpoint, e.g.

```
echo | nc localhost 9998
```

This is a command-line tool to allow easy reload 

shell or python to have a toggleable/managed command.

can be spawned off using multiprocessing.

Helper for chained/fast reload workflows.

Wraps a command and executes it, managing the execution and providing an interface for
killing and reloading it.

Only works on unix.

Features:

- pass-thru signals to underlying application
- accepts tcp or signal for reloading program
- accepts several methods of stopping program
  - --sigkill
  - --sigterm
- stdin/stdout transparently pass-thru
- allows tty communication?
- easy manual reload - signal

Usage:

```
reload --tcp 8080 'my command'
```

Reference:

- compatibility back to Python 2.7
- any data sent to listening endpoint results in process getting restarted
- Ctrl-C (SIGINT) sent to process results in process and listener being terminated,
  signal is passed-thru to child, same with subsequent Ctrl-C
- command can be anything valid in shell
- sigquit (`Ctrl-\`) sent to command will result in reload of application or restart of application
- Enter sent to command when not running will result in restart of command
- Ctrl-C send to process when not running will quit
- stdin/stdout are sent to application when running
