# Generate fixed routes for intersection crossing
routes = [
    "1311884249 1076976067#0",  # South to North
    "669017971 -669017971",     # West to East
    "-127506892#0 127506892#0",  # East to West
    "669017971 127506892#0",    # West to West
    "-127506892#0 1076976067#0", # East to North
    "1311884249 127506892#0"    # South to West
]

# Vehicle types with composition for 2000 vehicles
vehicle_types = [
    ("car_uv", 1280),  # 64% cars
    ("motorcycle", 300),  # 15% motorcycles
    ("jeepney", 200),  # 10% jeepneys
    ("bus_standard", 200),  # 10% buses
    ("ambulance", 34),  # part of 5% priority vehicles
    ("fire_truck", 33),  # part of 5% priority vehicles
    ("police", 33)  # part of 5% priority vehicles
]

# Generate vehicles with fixed routes, departing every 1.8 seconds
vehicles = []
vehicle_id = 0
route_index = 0

for vtype, count in vehicle_types:
    for i in range(count):
        route = routes[route_index % len(routes)]
        depart_time = vehicle_id * 1.8
        vehicles.append(f'    <vehicle id="{vehicle_id}" type="{vtype}" depart="{depart_time:.2f}" departPos="0">')
        vehicles.append(f'        <route edges="{route}"/>')
        vehicles.append('    </vehicle>')
        vehicle_id += 1
        route_index += 1

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

print("Generated random_routes.rou.xml with 2080 vehicles, fixed routes crossing the intersection.")
