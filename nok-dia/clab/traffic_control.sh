#!/bin/bash

# Configuration
SERVERS=("ns_eth1:1.1.1.11:5211")
#SERVERS=("ns_eth1:1.1.1.11:5211" "ns_eth2:1.1.1.12:5212")
CLIENTS=("ns_eth4" "ns_eth5" "ns_eth6" "ns_eth7")

# Standardized variables
DURATION=60
PARALLEL=4
WINDOW="4K"
MSS=1400

start_traffic() {
    echo "Starting iperf3 traffic..."
    for client in "${CLIENTS[@]}"; do
        for server in "${SERVERS[@]}"; do
            IFS=':' read -r _ SERVER_IP PORT <<< "$server"
            echo "  - Launching: $client -> $SERVER_IP:$PORT"
            
            # Using timeout to ensure cleanup, backgrounding with &
            docker exec -d clab-nok-dia-traffic-gen ip netns exec "$client" \
                timeout $((DURATION + 5)) \
                iperf3 -c "$SERVER_IP" -p "$PORT" -t "$DURATION" \
                -P "$PARALLEL" -w "$WINDOW" -M "$MSS" --connect-timeout 5000 \
                > /dev/null 2>&1
        done
    done
}

stop_traffic() {
    echo "Stopping all iperf3 processes..."
    for client in "${CLIENTS[@]}"; do
        docker exec clab-nok-dia-traffic-gen ip netns exec "$client" pkill iperf3
    done
}

usage() {
    echo "Usage: $0 {start|stop}"
    exit 1
}

# Ensure at least one argument is provided
if [ "$#" -ne 1 ]; then
    usage
fi

case "$1" in
    start) start_traffic ;;
    stop)  stop_traffic ;;
    *)     usage ;;
esac

echo "Operation complete."