import argparse
from stable_baselines3 import DQN
from sumo_env_dqn import SumoDQNEnv
import numpy as np
import time
try:
    import traci
except Exception as e:
    raise ImportError('traci required. Install SUMO and add tools to PYTHONPATH. ' + str(e))

def evaluate_model(model_path, sumo_config, num_episodes=10, max_steps=3600, min_green=5, gui=False, random=False, compare_fixed_time=False):
    env = SumoDQNEnv(sumo_config, max_steps=max_steps, min_green=min_green, gui=gui)
    if not random:
        model = DQN.load(model_path)

    # Initialize metrics lists
    rewards = []
    avg_delays = []
    priority_delays = []
    non_priority_delays = []
    avg_queues = []
    throughputs = []
    avg_travel_times = []

    # Additional simulation outcome metrics
    teleports = []
    jams = []
    yields = []
    wrong_lanes = []
    emergency_stops = []
    emergency_brakes = []

    # Vehicle statistics
    vehicles_inserted = []
    vehicles_running = []
    vehicles_waiting = []

    # Training performance metrics (if available)
    epsilon_values = []
    steps_per_episode = []
    simulation_times = []

    # For comparative evaluation
    fixed_time_rewards = []
    fixed_time_delays = []
    fixed_time_queues = []
    fixed_time_throughputs = []
    fixed_time_travel_times = []
    for episode in range(num_episodes):
        obs, _ = env.reset()
        done = False
        total_reward = 0.0
        step = 0
        delay_list = []
        priority_delay_list = []
        non_priority_delay_list = []
        queue_list = []
        departed_vehicles = []
        depart_times = {}
        arrive_times = {}
        while not done and step < max_steps:
            if random:
                action = env.action_space.sample()
            else:
                action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(int(action))
            done = terminated or truncated
            total_reward += reward
            # compute metrics
            try:
                all_vehs = traci.vehicle.getIDList()
                num_vehs = len(all_vehs)
                if num_vehs > 0:
                    total_wait = sum(traci.vehicle.getWaitingTime(v) for v in all_vehs)
                    avg_delay = total_wait / num_vehs
                    delay_list.append(avg_delay)
                    priority_vehs = [v for v in all_vehs if traci.vehicle.getVehicleClass(v) == 'emergency']
                    if priority_vehs:
                        priority_wait = sum(traci.vehicle.getWaitingTime(v) for v in priority_vehs)
                        priority_delay = priority_wait / len(priority_vehs)
                        priority_delay_list.append(priority_delay)
                        non_priority_vehs = [v for v in all_vehs if v not in priority_vehs]
                        if non_priority_vehs:
                            non_priority_wait = sum(traci.vehicle.getWaitingTime(v) for v in non_priority_vehs)
                            non_priority_delay = non_priority_wait / len(non_priority_vehs)
                            non_priority_delay_list.append(non_priority_delay)
                    else:
                        non_priority_delay_list.append(avg_delay)
                lanes = traci.trafficlight.getControlledLanes(env.tls)[:4]
                total_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
                avg_queue = total_queue / 4
                queue_list.append(avg_queue)
                # track departed (entering) and arrived (exiting)
                departed = traci.simulation.getDepartedIDList()  # entering vehicles
                for v in departed:
                    depart_times[v] = traci.simulation.getTime()  # entry time
                arrived = traci.simulation.getArrivedIDList()  # exiting vehicles
                for v in arrived:
                    arrive_times[v] = traci.simulation.getTime()  # exit time
                departed_vehicles.extend(arrived)

                # Additional simulation outcome metrics
                teleport_count = traci.simulation.getEndingTeleportIDList()
                teleports.append(len(teleport_count))

                # Jam detection (vehicles with speed < 0.1 m/s for extended periods)
                jam_count = sum(1 for v in all_vehs if traci.vehicle.getSpeed(v) < 0.1 and traci.vehicle.getWaitingTime(v) > 30)
                jams.append(jam_count)

                # Yield-related incidents (not directly available, using approximation)
                yield_count = sum(1 for v in all_vehs if traci.vehicle.getSpeed(v) < 1.0 and traci.vehicle.getWaitingTime(v) > 10)
                yields.append(yield_count)

                # Wrong lane incidents (vehicles not in their intended lane)
                wrong_lane_count = 0
                for v in all_vehs:
                    try:
                        intended_lane = traci.vehicle.getRouteIndex(v)
                        current_lane = traci.vehicle.getLaneIndex(v)
                        if intended_lane != current_lane:
                            wrong_lane_count += 1
                    except:
                        pass
                wrong_lanes.append(wrong_lane_count)

                # Emergency stops (sudden deceleration)
                emergency_stop_count = sum(1 for v in all_vehs if traci.vehicle.getAcceleration(v) < -4.0)
                emergency_stops.append(emergency_stop_count)

                # Emergency braking events (hard braking)
                emergency_brake_count = sum(1 for v in all_vehs if traci.vehicle.getAcceleration(v) < -3.0)
                emergency_brakes.append(emergency_brake_count)

                # Vehicle statistics
                vehicles_inserted.append(traci.simulation.getDepartedNumber())
                vehicles_running.append(traci.simulation.getRunningNumber())
                vehicles_waiting.append(sum(1 for v in all_vehs if traci.vehicle.getSpeed(v) < 0.1))

            except:
                pass
            step += 1
        rewards.append(total_reward)
        # compute episode metrics
        if delay_list:
            avg_delays.append(np.mean(delay_list))
        else:
            avg_delays.append(0.0)
        if priority_delay_list:
            priority_delays.append(np.mean(priority_delay_list))
        else:
            priority_delays.append(0.0)
        if non_priority_delay_list:
            non_priority_delays.append(np.mean(non_priority_delay_list))
        else:
            non_priority_delays.append(0.0)
        if queue_list:
            avg_queues.append(np.mean(queue_list))
        else:
            avg_queues.append(0.0)
        # throughput: vehicles per hour, exclude warm-up 600s
        eval_time = max_steps - 600
        throughput = len(departed_vehicles) / eval_time * 3600 if eval_time > 0 else 0.0
        throughputs.append(throughput)
        # travel time
        if departed_vehicles:
            travel_times = [arrive_times[v] - depart_times[v] for v in departed_vehicles if v in arrive_times and v in depart_times]
            avg_travel_time = np.mean(travel_times) if travel_times else 0.0
        else:
            avg_travel_time = 0.0
        avg_travel_times.append(avg_travel_time)
        print(f'Episode {episode+1}: Total reward {total_reward:.1f}, Avg Delay {avg_delays[-1]:.1f}, Priority Delay {priority_delays[-1]:.1f}, Non-Priority Delay {non_priority_delays[-1]:.1f}, Avg Queue {avg_queues[-1]:.1f}, Throughput {throughputs[-1]:.3f}, Avg Travel Time {avg_travel_times[-1]:.1f}')
    env.close()
    print(f'Average Reward: {np.mean(rewards):.1f} ± {np.std(rewards):.1f}')
    print(f'Average Delay: {np.mean(avg_delays):.1f} ± {np.std(avg_delays):.1f}')
    print(f'Average Priority Delay: {np.mean(priority_delays):.1f} ± {np.std(priority_delays):.1f}')
    print(f'Average Non-Priority Delay: {np.mean(non_priority_delays):.1f} ± {np.std(non_priority_delays):.1f}')
    print(f'Average Queue: {np.mean(avg_queues):.1f} ± {np.std(avg_queues):.1f}')
    print(f'Average Throughput: {np.mean(throughputs):.3f} ± {np.std(throughputs):.3f}')
    print(f'Average Travel Time: {np.mean(avg_travel_times):.1f} ± {np.std(avg_travel_times):.1f}')

    # Print vehicle statistics
    print(f'\nVehicle Statistics:')
    print(f'Average Vehicles Inserted: {np.mean(vehicles_inserted):.1f} ± {np.std(vehicles_inserted):.1f}')
    print(f'Average Vehicles Running: {np.mean(vehicles_running):.1f} ± {np.std(vehicles_running):.1f}')
    print(f'Average Vehicles Waiting: {np.mean(vehicles_waiting):.1f} ± {np.std(vehicles_waiting):.1f}')

    # Print additional simulation outcome metrics
    print(f'\nSimulation Outcomes:')
    print(f'Average Teleports: {np.mean(teleports):.1f} ± {np.std(teleports):.1f}')
    print(f'Average Jams: {np.mean(jams):.1f} ± {np.std(jams):.1f}')
    print(f'Average Yield Incidents: {np.mean(yields):.1f} ± {np.std(yields):.1f}')
    print(f'Average Wrong Lane Incidents: {np.mean(wrong_lanes):.1f} ± {np.std(wrong_lanes):.1f}')
    print(f'Average Emergency Stops: {np.mean(emergency_stops):.1f} ± {np.std(emergency_stops):.1f}')
    print(f'Average Emergency Braking Events: {np.mean(emergency_brakes):.1f} ± {np.std(emergency_brakes):.1f}')

    # Training performance metrics (limited info available during evaluation)
    print(f'\nTraining Performance (DQN):')
    print(f'Steps per Episode: {max_steps} (fixed)')
    print(f'Epsilon: N/A (evaluation mode)')
    print(f'Simulation Time per Episode: ~{max_steps/3600:.1f} hours (at real-time)')

    # Run comparative evaluation if requested
    if compare_fixed_time:
        print(f'\n--- Running Fixed-Time Control Comparison ---')
        fixed_time_avg_reward, fixed_time_std_reward = run_fixed_time_evaluation(sumo_config, num_episodes, max_steps, min_green, gui)

        # Print comparative results
        print(f'\nComparative Evaluation (DQN vs Fixed-Time):')
        print(f'DQN Average Reward: {np.mean(rewards):.1f} ± {np.std(rewards):.1f}')
        print(f'Fixed-Time Average Reward: {fixed_time_avg_reward:.1f} ± {fixed_time_std_reward:.1f}')
        print(f'Reward Improvement: {np.mean(rewards) - fixed_time_avg_reward:.1f} ({((np.mean(rewards) - fixed_time_avg_reward) / abs(fixed_time_avg_reward) * 100):.1f}%)')

        if fixed_time_delays:
            print(f'DQN Average Delay: {np.mean(avg_delays):.1f} ± {np.std(avg_delays):.1f}')
            print(f'Fixed-Time Average Delay: {np.mean(fixed_time_delays):.1f} ± {np.std(fixed_time_delays):.1f}')
            print(f'Delay Reduction: {np.mean(fixed_time_delays) - np.mean(avg_delays):.1f} ({((np.mean(fixed_time_delays) - np.mean(avg_delays)) / abs(np.mean(fixed_time_delays)) * 100):.1f}%)')

        if fixed_time_queues:
            print(f'DQN Average Queue: {np.mean(avg_queues):.1f} ± {np.std(avg_queues):.1f}')
            print(f'Fixed-Time Average Queue: {np.mean(fixed_time_queues):.1f} ± {np.std(fixed_time_queues):.1f}')
            print(f'Queue Reduction: {np.mean(fixed_time_queues) - np.mean(avg_queues):.1f} ({((np.mean(fixed_time_queues) - np.mean(avg_queues)) / abs(np.mean(fixed_time_queues)) * 100):.1f}%)')

        if fixed_time_throughputs:
            print(f'DQN Average Throughput: {np.mean(throughputs):.3f} ± {np.std(throughputs):.3f}')
            print(f'Fixed-Time Average Throughput: {np.mean(fixed_time_throughputs):.3f} ± {np.std(fixed_time_throughputs):.3f}')
            print(f'Throughput Improvement: {np.mean(throughputs) - np.mean(fixed_time_throughputs):.3f} ({((np.mean(throughputs) - np.mean(fixed_time_throughputs)) / abs(np.mean(fixed_time_throughputs)) * 100):.1f}%)')

        if fixed_time_travel_times:
            print(f'DQN Average Travel Time: {np.mean(avg_travel_times):.1f} ± {np.std(avg_travel_times):.1f}')
            print(f'Fixed-Time Average Travel Time: {np.mean(fixed_time_travel_times):.1f} ± {np.std(fixed_time_travel_times):.1f}')
            print(f'Travel Time Reduction: {np.mean(fixed_time_travel_times) - np.mean(avg_travel_times):.1f} ({((np.mean(fixed_time_travel_times) - np.mean(avg_travel_times)) / abs(np.mean(fixed_time_travel_times)) * 100):.1f}%)')

    return np.mean(rewards), np.std(rewards)

def run_fixed_time_evaluation(sumo_config, num_episodes=10, max_steps=3600, min_green=5, gui=False):
    """Run fixed-time control evaluation for comparison"""
    from sumo_env_dqn import SumoDQNEnv

    env = SumoDQNEnv(sumo_config, max_steps=max_steps, min_green=min_green, gui=gui, fixed_time=True)

    rewards = []
    delays = []
    queues = []
    throughputs = []
    travel_times = []

    for episode in range(num_episodes):
        obs, _ = env.reset()
        done = False
        total_reward = 0.0
        step = 0
        delay_list = []
        queue_list = []
        departed_vehicles = []
        depart_times = {}
        arrive_times = {}

        while not done and step < max_steps:
            # Fixed-time control: use predefined phase durations
            action = 0  # Fixed-time doesn't change phases dynamically
            obs, reward, terminated, truncated, _ = env.step(int(action))
            done = terminated or truncated
            total_reward += reward

            # Compute basic metrics for comparison
            try:
                all_vehs = traci.vehicle.getIDList()
                num_vehs = len(all_vehs)
                if num_vehs > 0:
                    total_wait = sum(traci.vehicle.getWaitingTime(v) for v in all_vehs)
                    avg_delay = total_wait / num_vehs
                    delay_list.append(avg_delay)

                lanes = traci.trafficlight.getControlledLanes(env.tls)[:4]
                total_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
                avg_queue = total_queue / 4
                queue_list.append(avg_queue)

                # Track vehicles for throughput and travel time
                departed = traci.simulation.getDepartedIDList()
                for v in departed:
                    depart_times[v] = traci.simulation.getTime()
                arrived = traci.simulation.getArrivedIDList()
                for v in arrived:
                    arrive_times[v] = traci.simulation.getTime()
                departed_vehicles.extend(arrived)

            except:
                pass
            step += 1

        rewards.append(total_reward)
        if delay_list:
            delays.append(np.mean(delay_list))
        if queue_list:
            queues.append(np.mean(queue_list))

        # Throughput calculation
        eval_time = max_steps - 600
        throughput = len(departed_vehicles) / eval_time * 3600 if eval_time > 0 else 0.0
        throughputs.append(throughput)

        # Travel time calculation
        if departed_vehicles:
            travel_times_list = [arrive_times[v] - depart_times[v] for v in departed_vehicles if v in arrive_times and v in depart_times]
            avg_travel_time = np.mean(travel_times_list) if travel_times_list else 0.0
        else:
            avg_travel_time = 0.0
        travel_times.append(avg_travel_time)

        print(f'Fixed-Time Episode {episode+1}: Total reward {total_reward:.1f}, Avg Delay {delays[-1]:.1f}, Avg Queue {queues[-1]:.1f}, Throughput {throughputs[-1]:.3f}, Avg Travel Time {travel_times[-1]:.1f}')

    env.close()

    # Store results in global lists for comparison
    global fixed_time_rewards, fixed_time_delays, fixed_time_queues, fixed_time_throughputs, fixed_time_travel_times
    fixed_time_rewards = rewards
    fixed_time_delays = delays
    fixed_time_queues = queues
    fixed_time_throughputs = throughputs
    fixed_time_travel_times = travel_times

    print(f'Fixed-Time Average Reward: {np.mean(rewards):.1f} ± {np.std(rewards):.1f}')
    print(f'Fixed-Time Average Delay: {np.mean(delays):.1f} ± {np.std(delays):.1f}')
    print(f'Fixed-Time Average Queue: {np.mean(queues):.1f} ± {np.std(queues):.1f}')
    print(f'Fixed-Time Average Throughput: {np.mean(throughputs):.3f} ± {np.std(throughputs):.3f}')
    print(f'Fixed-Time Average Travel Time: {np.mean(travel_times):.1f} ± {np.std(travel_times):.1f}')

    return np.mean(rewards), np.std(rewards)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--sumo-config', required=True)
    parser.add_argument('--num-episodes', type=int, default=10)
    parser.add_argument('--max-steps', type=int, default=3600)
    parser.add_argument('--min-green', type=int, default=5)
    parser.add_argument('--gui', action='store_true', help='Enable SUMO GUI')
    parser.add_argument('--random', action='store_true', help='Use random actions instead of model')
    parser.add_argument('--compare-fixed-time', action='store_true', help='Compare with fixed-time control')
    parser.add_argument('--scenario', choices=['light', 'moderate', 'heavy', 'mixed'], help='Traffic demand scenario to evaluate')
    args = parser.parse_args()

    if args.scenario:
        run_scenario_evaluation(args.model, args.scenario, args.num_episodes, args.max_steps, args.min_green, args.gui, args.random)
    else:
        evaluate_model(args.model, args.sumo_config, args.num_episodes, args.max_steps, args.min_green, args.gui, args.random, args.compare_fixed_time)

def run_scenario_evaluation(model_path, scenario, num_episodes=10, max_steps=3600, min_green=5, gui=False, random=False):
    """Run evaluation for different traffic demand scenarios"""
    from stable_baselines3 import DQN

    # Define scenario configurations
    scenario_configs = {
        'light': 'light_traffic.sumocfg',
        'moderate': 'moderate_traffic.sumocfg',
        'heavy': 'heavy_traffic.sumocfg',
        'mixed': 'mixed_traffic.sumocfg'
    }

    if scenario not in scenario_configs:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(scenario_configs.keys())}")

    config_file = scenario_configs[scenario]

    print(f'\n--- Evaluating {scenario.capitalize()} Traffic Scenario ---')
    print(f'Using configuration: {config_file}')

    # Check if config file exists, if not create a basic one
    try:
        with open(config_file, 'r') as f:
            pass
    except FileNotFoundError:
        print(f'Warning: {config_file} not found. Using default configuration.')
        config_file = 'simple.sumocfg'  # fallback

    # Run evaluation
    avg_reward, std_reward = evaluate_model(model_path, config_file, num_episodes, max_steps, min_green, gui, random, False)

    print(f'\n{scenario.capitalize()} Scenario Results:')
    print(f'Average Reward: {avg_reward:.1f} ± {std_reward:.1f}')

    return avg_reward, std_reward
