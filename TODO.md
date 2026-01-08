# TODO for Traffic Optimization Simulation

## 1. Update Vehicle Generation
- [x] Modify generate_routes.py to adjust departure time spacing to ~1.8 seconds per vehicle using random.uniform(1.5, 2.1).
- [x] Correct the print statement to reflect actual vehicle count (2080).

## 2. Update Simulation Configuration
- [x] Edit simple.sumocfg to set end time to 3600 seconds.

## 3. Update Evaluation Script
- [x] Edit evaluate_model.py to set default max_steps to 3600.

## 4. Regenerate Routes
- [x] Run updated generate_routes.py to create new random_routes.rou.xml.

## 5. Clean Up Unnecessary Files
- [x] Delete unnecessary route files: old_routes.rou.xml, routes.rou.alt.xml, routes.rou.backup.xml, new_routes.rou.xml, trips.trips.xml.

## 6. Run Training
- [x] Execute train_dqn.py with --sumo-config simple.sumocfg --timesteps 720000 --episode-length 3600 --seed 42.

## 7. Clean Map
- [x] Retain only 2 vertical lanes in the middle and 1 horizontal lane, remove excess lanes using netconvert.
- [x] Fix internal edge connections and lane indices for proper traffic light functionality.
- [x] Change junctions C and D to priority type with appropriate incLanes.

## 8. Evaluate Model
- [x] Run evaluate_model.py on the trained model with --max-steps 3600.

## 9. Extend Evaluation Script
- [x] Add vehicle statistics tracking (vehicles_inserted, vehicles_running, vehicles_waiting).
- [x] Implement comparative evaluation (Fixed-Time vs DQN) with --compare-fixed-time flag.
- [x] Add scenario variation support with --scenario flag for light/moderate/heavy/mixed traffic.
- [x] Update SumoDQNEnv to support fixed_time parameter for baseline comparisons.
