def psuedo_code_example():
    """Compare to the current implementation of start()"""
    class Service:
        def start(self, block_until_ready=True):
            self.state("start_services")
            for child in self._children:
                child.start(block_until_ready)
            self.state("services_started")
            ready = not self.do_start()
            if not ready and block_until_ready:
                self.state.wait("ready", self.ready_timeout)
            elif ready:
                self.state("ready")
            # if not ready, but block_until_ready is false,
            # your service code will just call self.state("ready")
            # when ready. this replaces self.set_ready()

class ServiceStateManager(object):
    def __init__(self, service):
        self.state = "init"
        self._service = service
        self._events = {
            "ready": Event(),
            "stopped": Event(),
        }

    def _callback(self, name):
        if hasattr(self._service, name):
            getattr(self._service, name)()

    def _transition(self, new_state):
        for state in self._events:
            self._events[state].clear()
        self.state = new_state
        if new_state in self._events:
            self._events[new_state].set()

    def wait(self, state, timeout=None):
        self._events[state].wait(timeout)

    def __call__(self, event):
        trigger = "event_{}".format(event)
        if hasattr(self, trigger):
            getattr(self, trigger)()
        else:
            raise AttributeError("No event '{}'".format(event))

    # Event triggers

    def event_start_services(self):
        if self.state in ["init", "stopped"]:
            self._callback("pre_start")
            self._transition("starting:services")

    def event_services_started(self):
        if self.state in ["starting:services"]:
            self._transition("starting")

    def event_ready(self):
        if self.state in ["starting"]:
            self._callback("post_start")
            self._transition("ready")

    def event_stop_services(self):
        if self.state in ["ready", "starting:services", "starting"]:
            self._callback("pre_stop")
            self._transition("stopping:services")

    def event_services_stopped(self):
        if self.state in ["stopping:services"]:
            self._transition("stopping")

    def event_stopped(self):
        if self.state in ["stopping", "stopping:services"]:
            self._callback("post_stop")
            self._transition("stopped")