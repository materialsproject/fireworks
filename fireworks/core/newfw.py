class Firework(FWSerializable):
    """
    A Firework is a workflow step and might be contain several Firetasks.
    It contains the Firetasks to be executed and the state of the execution.
    """

    STATE_RANKS = {'ARCHIVED': -2, 'FIZZLED': -1, 'DEFUSED': 0, 'PAUSED' : 0,
                   'WAITING': 1, 'READY': 2, 'RESERVED': 3, 'RUNNING': 4,
                   'COMPLETED': 5}

    def __init__(self, tasks, launch_dir=None, spec=None, name=None, state='WAITING',
                 fworker=None, host=None, ip=None, trackers=None,
                 fw_id=None, parents=None, created_on=None, updated_on=None,
                 action=None, state_history=None):

    	self.tasks = tasks
    	self.spec = spec.copy() if spec else {}
    	self.name = name or 'Unnamed FW'
    	# names
    	if fw_id is not None:
    		self.fw_id = wf_id
    	else:
    		global NEGATIVE_FWID_CTR
    		NEGATIVE_FWID_CTR -= 1
    		self.fw_id = NEGATIVE_FWID_CTR

    	self.launch_dir = launch_dir or os.getcwd()

    	self._state = state
    	self.parents = parents if parents else []
    	self.created_on = created_on or datetime.utcnow()
    	self.updated_on = updated_on or datetime.utcnow()

    	self.fworker = fworker or FWorker()
    	self.host = host or get_my_host()
    	self.ip = ip or get_my_ip()
    	self.trackers = trackers if trackers else []

    	self.action = action if action else None
    	self.state_history = state_history if state_history else []

    # FUNCTIONS FOR ACCESSING AND UPDATING STATE HISTORY

    def touch_history(self, update_time=None, checkpoint=None):
        """
        Updates the update_on field of the state history of a Launch. Used to ping that a Launch
        is still alive.

        Args:
            update_time (datetime)
        """
        update_time = update_time or datetime.utcnow()
        if checkpoint:
            self.state_history[-1]['checkpoint'] = checkpoint
        self.state_history[-1]['updated_on'] = update_time
        self.updated_on = update_time

    def _update_state_history(self, state):
        """
        Internal method to update the state history whenever the Launch state is modified.

        Args:
            state (str)
        """
        if len(self.state_history) > 0:
            last_state = self.state_history[-1]['state']
            last_checkpoint = self.state_history[-1].get('checkpoint', None)
        else:
            last_state, last_checkpoint = None, None
        if state != last_state:
            now_time = datetime.utcnow()
            new_history_entry = {'state': state, 'created_on': now_time}
            if state != "COMPLETED" and last_checkpoint:
                new_history_entry.update({'checkpoint': last_checkpoint})
            self.state_history.append(new_history_entry)
            if state in ['RUNNING', 'RESERVED']:
                self.touch_history()  # add updated_on key

    def _get_time(self, states, use_update_time=False):
        """
        Internal method to help get the time of various events in the Launch (e.g. RUNNING)
        from the state history.

        Args:
            states (list/tuple): match one of these states
            use_update_time (bool): use the "updated_on" time rather than "created_on"

        Returns:
            (datetime)
        """
        states = states if isinstance(states, (list, tuple)) else [states]
        for data in self.state_history:
            if data['state'] in states:
                if use_update_time:
                    return data['updated_on']
                return data['created_on']

    def set_reservation_id(self, reservation_id):
        """
        Adds the job_id to the reservation.

        Args:
            reservation_id (int or str): the id of the reservation (e.g., queue reservation)
        """
        for data in self.state_history:
            if data['state'] == 'RESERVED' and 'reservation_id' not in data:
                data['reservation_id'] = str(reservation_id)
                break

    @property
    def state(self):
        """
        Returns:
            str: The current state of the Launch.
        """
        return self._state

    @state.setter
    def state(self, state):
        """
        Setter for the the Launch's state. Automatically triggers an update to state_history.

        Args:
            state (str): the state to set for the Launch
        """
        self._state = state
        self._update_state_history(state)

    @property
    def time_start(self):
        """
        Returns:
            datetime: the time the Launch started RUNNING
        """
        return self._get_time('RUNNING')

    @property
    def time_end(self):
        """
        Returns:
            datetime: the time the Launch was COMPLETED or FIZZLED
        """
        return self._get_time(['COMPLETED', 'FIZZLED'])

    @property
    def time_reserved(self):
        """
        Returns:
            datetime: the time the Launch was RESERVED in the queue
        """
        return self._get_time('RESERVED')

    @property
    def last_pinged(self):
        """
        Returns:
            datetime: the time the Launch last pinged a heartbeat that it was still running
        """
        return self._get_time('RUNNING', True)

    @property
    def runtime_secs(self):
        """
        Returns:
            int: the number of seconds that the Launch ran for.
        """
        start = self.time_start
        end = self.time_end
        if start and end:
            return (end - start).total_seconds()

    @property
    def reservedtime_secs(self):
        """
        Returns:
            int: number of seconds the Launch was stuck as RESERVED in a queue.
        """
        start = self.time_reserved
        if start:
            end = self.time_start if self.time_start else datetime.utcnow()
            return (end - start).total_seconds()

    @recursive_serialize
    def to_dict(self):
        # put tasks in a special location of the spec
        spec = self.spec
        spec['_tasks'] = [t.to_dict() for t in self.tasks]
        m_dict = {'spec': spec,
                  'name': self.name
                  'fw_id': self.fw_id,
                  'fworker': self.fworker,
	              'launch_dir': self.launch_dir,
	              'host': self.host,
	              'ip': self.ip,
	              'trackers': self.trackers,
	              'action': self.action,
	              'state': self.state,
	              'state_history': self.state_history,
	              'created_on': self.created_on,
	              'updated_on': self.updated_on}

        return m_dict

    @recursive_serialize
    def to_db_dict(self):
    	m_d = self.to_dict()
        m_d['time_start'] = self.time_start
        m_d['time_end'] = self.time_end
        m_d['runtime_secs'] = self.runtime_secs
        if self.reservedtime_secs:
            m_d['reservedtime_secs'] = self.reservedtime_secs
        return m_d

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        tasks = m_dict['spec']['_tasks']
        fw_id = m_dict.get('fw_id', -1)
        state = m_dict.get('state', 'WAITING')
        created_on = m_dict.get('created_on')
        updated_on = m_dict.get('updated_on')
        name = m_dict.get('name', None)
        fworker = FWorker.from_dict(m_dict['fworker']) if m_dict['fworker'] else None
        action = FWAction.from_dict(m_dict['action']) if m_dict.get('action') else None
        trackers = [Tracker.from_dict(f) for f in m_dict['trackers']] if m_dict.get('trackers') else None
        return Firework(tasks, m_dict['launch_dir'], m_dict['spec'], name, state,
                        fworker, m_dict['host'], m_dict['ip'], trackers,
                        fw_id, m_dict['parents'], created_on, updated_on,
                        action, m_dict['state_history'])

    def __str__(self):
        return 'Firework object: (id: %i , name: %s)' % (self.fw_id, self.fw_name)
