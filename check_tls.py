import traci

# Start SUMO with the new config
traci.start(['sumo', '-c', 'temp.sumocfg', '--step-length', '1.0'])

# Get list of traffic lights
tls_list = traci.trafficlight.getIDList()
print(f"Traffic lights found: {tls_list}")

# For each traffic light, print controlled lanes
for tls_id in tls_list:
    lanes = traci.trafficlight.getControlledLanes(tls_id)
    print(f"Traffic light {tls_id} controls lanes: {lanes}")

# Close
traci.close()
