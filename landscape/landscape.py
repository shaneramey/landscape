"""Landscape class to handle deployments of clusters and Landscaper configs."""

class Landscape(object):
    """Deploys Kubernetes clusters and Helm charts

    Arguments:
        log(logger obj): A logger to log messages.

        config(configparger obj): A configparser object with the configuration

        action(Queue obj): A queue of IP prefixes and their action to be taken
        based on the state of health check. An item is a tuple of 3 elements:
        1st: name of the thread.
        2nd: IP prefix.
        3nd: Action to take, either 'add' or 'del'.

    Methods:
        run(): Lunches checks and updates BIRD configuration based on
        the result of the check.
        catch_signal(signum, frame): Catches signals
    """
    
    def __init__(self):
        print "placeholder"