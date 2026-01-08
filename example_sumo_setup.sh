#!/usr/bin/env bash
set -e
echo "Generating a small grid network (1x1 intersection)..."
netgenerate --grid --grid.number=1 --default.lanenumber=1 -o net.net.xml
echo "Generating random trips (100 vehicles)..."
python3 $(which randomTrips.py) -n net.net.xml -o trips.trips.xml -r routes.rou.xml -e 200 -p 1.0
echo "Converting trips to routes..."
duarouter -n net.net.xml -t trips.trips.xml -o routes.rou.xml
cat > simple.sumocfg <<EOL
<configuration>
  <input>
    <net-file value="net.net.xml"/>
    <route-files value="routes.rou.xml"/>
  </input>
  <time>
    <begin value="0"/>
    <end value="1000"/>
  </time>
</configuration>
EOL
echo "Done. Files: net.net.xml, routes.rou.xml, simple.sumocfg"
