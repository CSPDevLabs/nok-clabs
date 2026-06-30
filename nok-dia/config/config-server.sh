#!/bin/bash

# 1. Create network namespaces
ip netns add ns_eth1
ip netns add ns_eth2
ip netns add ns_eth4
ip netns add ns_eth5
ip netns add ns_eth6
ip netns add ns_eth7

# 2. Assign interfaces to namespaces
ip link set eth1 netns ns_eth1
ip link set eth2 netns ns_eth2
ip link set eth4 netns ns_eth4
ip link set eth5 netns ns_eth5
ip link set eth6 netns ns_eth6
ip link set eth7 netns ns_eth7

# 3. Bring interfaces up and assign IP addresses inside namespaces
ip netns exec ns_eth1 ip link set eth1 up
ip netns exec ns_eth1 ip addr add 1.1.1.11/24 dev eth1
ip netns exec ns_eth1 ip route add default via 1.1.1.254

ip netns exec ns_eth2 ip link set eth2 up
ip netns exec ns_eth2 ip addr add 1.1.1.12/24 dev eth2
ip netns exec ns_eth2 ip route add default via 1.1.1.254

ip netns exec ns_eth4 ip link set eth4 up
ip netns exec ns_eth4 ip addr add 198.18.1.4/28 dev eth4
ip netns exec ns_eth4 ip route add default via 198.18.1.1

ip netns exec ns_eth5 ip link set eth5 up
ip netns exec ns_eth5 ip addr add 198.18.1.5/28 dev eth5
ip netns exec ns_eth5 ip route add default via 198.18.1.1

ip netns exec ns_eth6 ip link set eth6 up
ip netns exec ns_eth6 ip addr add 198.18.1.6/28 dev eth6
ip netns exec ns_eth6 ip route add default via 198.18.1.1

ip netns exec ns_eth7 ip link set eth7 up
ip netns exec ns_eth7 ip addr add 198.18.1.7/28 dev eth7
ip netns exec ns_eth7 ip route add default via 198.18.1.1

# 4. Bring up loopback interfaces inside namespaces (required by iperf3)
ip netns exec ns_eth1 ip link set lo up
ip netns exec ns_eth2 ip link set lo up
ip netns exec ns_eth4 ip link set lo up
ip netns exec ns_eth5 ip link set lo up
ip netns exec ns_eth6 ip link set lo up
ip netns exec ns_eth7 ip link set lo up

# 5. Start iperf3 servers in background daemon mode inside their namespaces
# Binding to the specific IP ensures it only listens on that interface
ip netns exec ns_eth1 iperf3 -s -B 1.1.1.11 -p 5211 -D
ip netns exec ns_eth2 iperf3 -s -B 1.1.1.12 -p 5212 -D