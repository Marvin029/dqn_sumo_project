import random

# Cycling routes for vehicles to cycle within roads using endpoints
# Each route goes from one end to the other and back, allowing cycling
cycling_routes = [
    "A2B B2A",  # A to B and back
    "A2C C2A",  # A to C and back
    "B2D D2B",  # B to D and back
    "C2D D2C",  # C to D and back
    "A2B B2D D2B B2A",  # A to B to D and back
    "A2C C2D D2C C2A",  # A to C to D and back
    "B2A A2C C2A A2B B2A",  # B to A to C and back to B
    "D2B B2A A2B B2D D2B",  # D to B to A and back to D
    "D2C C2A A2C C2D D2C",  # D to C to A and back to D
    "B2D D2C C2D D2B B2D"   # B to D to C and back to B
]

# Vehicle types with composition for ~2000 vehicles
vehicle_types = [
    ("car_uv", 1280),  # 64% cars
    ("motorcycle", 300),  # 15% motorcycles
    ("jeepney", 200),  # 10% jeepneys
    ("bus_standard", 200),  # 10% buses
    ("ambulance", 34),  # part of 5% priority vehicles
    ("fire_truck", 33),  # part of 5% priority vehicles
    ("police", 33)  # part of 5% priority vehicles
]

# Generate vehicles with random cycling routes
vehicles = []
vehicle_id = 0
depart_time = 0

for vtype, count in vehicle_types:
    for i in range(count):
        route = random.choice(cycling_routes)  # Random cycling route
        vehicles.append(f'    <vehicle id="{vehicle_id}" type="{vtype}" depart="{depart_time:.2f}" departPos="random" departLane="random">')
        vehicles.append(f'        <route edges="{route}"/>')
        vehicles.append('    </vehicle>')
        vehicle_id += 1
        depart_time += random.uniform(1.5, 2.1)  # Random spacing

# Write to file
with open("random_routes.rou.xml", "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
    f.write('\n    <!-- Vehicle Types -->\n')
    f.write('    <vType id="car_uv" vClass="passenger" guiShape="passenger" accel="2.6" decel="4.5" sigma="0.5" length="7.0" width="3.0" maxSpeed="15" color="0,0,1"/>\n')
    f.write('    <vType id="motorcycle" vClass="motorcycle" guiShape="motorcycle" accel="2.2" decel="4.0" sigma="0.5" length="4.0" width="1.5" maxSpeed="12" color="1,0,0"/>\n')
    f.write('    <vType id="jeepney" vClass="bus" guiShape="delivery" accel="1.5" decel="3.0" sigma="0.5" length="9.0" width="3.5" maxSpeed="10" color="0,1,0"/>\n')
    f.write('    <vType id="bus_standard" vClass="bus" guiShape="bus" accel="1.2" decel="2.5" sigma="0.5" length="16.0" width="4.0" maxSpeed="8" color="1,0.5,0"/>\n')
    f.write('    <vType id="tricycle" vClass="moped" guiShape="moped" accel="1.8" decel="3.5" sigma="0.5" length="5.0" width="2.0" maxSpeed="7" color="0.5,0,0.5"/>\n')
    f.write('    <vType id="ambulance" vClass="emergency" guiShape="emergency" accel="3.0" decel="4.0" sigma="0.3" length="8.0" width="3.0" maxSpeed="20" color="1,1,1"/>\n')
    f.write('    <vType id="fire_truck" vClass="emergency" guiShape="truck" accel="2.0" decel="3.0" sigma="0.3" length="13.0" width="3.5" maxSpeed="15" color="1,0,0"/>\n')
    f.write('    <vType id="police" vClass="emergency" guiShape="emergency" accel="2.8" decel="4.0" sigma="0.3" length="7.0" width="2.5" maxSpeed="18" color="0,0,0"/>\n')
    f.write('\n')
    f.write('\n'.join(vehicles))
    f.write('\n</routes>\n')

print("Generated random_routes.rou.xml with 2080 vehicles, fixed multi-edge routes for turns, random departure times, starting at lane beginnings.")
