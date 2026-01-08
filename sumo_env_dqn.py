# sumo_env_dqn.py
import numpy as np, gymnasium as gym
from gymnasium import spaces
try:
    import traci
except Exception as e:
    raise ImportError('traci required. Install SUMO and add tools to PYTHONPATH. ' + str(e))

class SumoDQNEnv(gym.Env):
    def __init__(self, sumo_cfg, tls_id=None, step_length=1.0, max_steps=1000, min_green=5, gui=False, fixed_time=False):
        super().__init__()
        self.sumo_cfg = sumo_cfg
        self.tls_id = tls_id
        self.step_length = step_length
        self.max_steps = max_steps
        self.min_green = min_green
        self.gui = gui
        self.fixed_time = fixed_time

        self.observation_space = spaces.Box(low=np.zeros(11,dtype=np.float32),
                                            high=np.array([1000]*4 + [60] + [1] + [10000] + [1000]*4, dtype=np.float32),
                                            dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self._connected = False
        self._step = 0

    def _get_tls_id(self):
        tls = traci.trafficlight.getIDList()
        if not tls:
            raise RuntimeError('No traffic lights found.')
        return tls[0] if self.tls_id is None else self.tls_id

    def _get_state_info(self, tls_id):
        lanes = traci.trafficlight.getControlledLanes(tls_id)
        queue_lengths = []
        waiting_times = []
        priority_counts = []
        for lane in lanes[:4]:
            try:
                vehs = traci.lane.getLastStepVehicleIDs(lane)
                halting = traci.lane.getLastStepHaltingNumber(lane)
                queue_lengths.append(halting)
                wait_sum = sum(traci.vehicle.getWaitingTime(v) for v in vehs)
                waiting_times.append(wait_sum)
                priority_count = sum(1 for v in vehs if traci.vehicle.getVehicleClass(v) == 'emergency')
                priority_counts.append(priority_count)
            except Exception:
                queue_lengths.append(0)
                waiting_times.append(0)
                priority_counts.append(0)
        while len(queue_lengths)<4:
            queue_lengths.append(0)
            waiting_times.append(0)
            priority_counts.append(0)
        total_wait = sum(waiting_times)
        total_priority = sum(priority_counts)
        return queue_lengths, total_wait, total_priority, priority_counts

    def reset(self, seed=None, options=None):
        if self._connected:
            try: traci.close()
            except Exception: pass
            self._connected = False
        sumo_cmd = 'sumo-gui' if self.gui else 'sumo'
        traci.start([sumo_cmd,'-c', self.sumo_cfg, '--step-length', str(self.step_length)])
        self._connected = True
        self._step = 0
        self.tls = self._get_tls_id()
        queue_lengths, total_wait, total_priority, priority_counts = self._get_state_info(self.tls)
        phase = 0.0  # initial NS green
        obs = np.array(queue_lengths + [phase] + [total_wait] + [total_priority] + priority_counts, dtype=np.float32)
        return obs, {}

    def step(self, action):
        tls = self._get_tls_id()
        # apply action
        switched = 0
        if self.fixed_time:
            # Fixed-time control: switch phases every 30 steps (30 seconds)
            if self._step % 30 == 0:
                switched = 1
                try:
                    current_phase = traci.trafficlight.getPhase(tls)
                    if current_phase in [0, 1]:  # NS green
                        traci.trafficlight.setPhase(tls, 2)  # EW green
                    else:
                        traci.trafficlight.setPhase(tls, 0)  # NS green
                except Exception:
                    pass
            total_step = 1  # Step by 1 in fixed-time
        else:
            if action == 1:  # switch
                switched = 1
                try:
                    current_phase = traci.trafficlight.getPhase(tls)
                    if current_phase in [0, 1]:  # NS green
                        traci.trafficlight.setPhase(tls, 2)  # EW green
                    else:
                        traci.trafficlight.setPhase(tls, 0)  # NS green
                except Exception:
                    pass
            # advance simulation
            if action == 0:  # extend
                total_step = 5
            else:  # switch
                total_step = int(self.min_green) + 3
        try:
            total_wait_start = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList())
            emergency_wait_start = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList() if traci.vehicle.getVehicleClass(v) == 'emergency')
            num_vehicles_start = len(traci.vehicle.getIDList())
            priority_vehicles_start = sum(1 for v in traci.vehicle.getIDList() if traci.vehicle.getVehicleClass(v) == 'emergency')
            queue_lengths_start = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in traci.trafficlight.getControlledLanes(tls)[:4])
        except Exception:
            total_wait_start = 0
            emergency_wait_start = 0
            num_vehicles_start = 0
            priority_vehicles_start = 0
            queue_lengths_start = 0
        terminated = False
        try:
            for _ in range(total_step):
                traci.simulationStep()
                self._step += 1
        except Exception:
            terminated = True
        try:
            total_wait_end = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList())
            emergency_wait_end = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList() if traci.vehicle.getVehicleClass(v) == 'emergency')
            num_vehicles_end = len(traci.vehicle.getIDList())
            priority_vehicles_end = sum(1 for v in traci.vehicle.getIDList() if traci.vehicle.getVehicleClass(v) == 'emergency')
            queue_lengths_end = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in traci.trafficlight.getControlledLanes(tls)[:4])
            # compute reward
            avg_delay = total_wait_end / num_vehicles_end if num_vehicles_end > 0 else 0
            avg_queue = queue_lengths_end / 4
            priority_delay = emergency_wait_end / priority_vehicles_end if priority_vehicles_end > 0 else 0
            normalized_avg_delay = avg_delay / 60.0
            normalized_avg_queue = avg_queue / 20.0
            normalized_priority_delay = priority_delay / 60.0
            reward = - (1.0 * normalized_avg_delay + 0.5 * normalized_avg_queue) - 0.1 * switched - 2.0 * normalized_priority_delay
        except Exception:
            reward = 0
            terminated = True
        terminated = terminated or self._step >= self.max_steps or (num_vehicles_end == 0 and self._step > 100)
        if terminated:
            print(f"Terminated: step {self._step}, max_steps {self.max_steps}, vehicles {num_vehicles_end}")
        truncated = False
        try:
            queue_lengths, total_wait, total_priority, priority_counts = self._get_state_info(tls)
            try:
                phase = traci.trafficlight.getPhase(tls)
                phase_val = 0.0 if phase in [0, 1] else 1.0
            except Exception:
                phase_val = 0.0
            obs = np.array(queue_lengths + [total_wait] + [phase_val] + [total_priority] + priority_counts, dtype=np.float32)
        except Exception:
            obs = np.zeros(11, dtype=np.float32)
            terminated = True
        return obs, reward, terminated, truncated, {}

    def render(self, mode='human'):
        pass

    def close(self):
        if self._connected:
            try: traci.close()
            except Exception: pass
            self._connected = False
