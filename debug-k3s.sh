#!/bin/bash
sudo /usr/local/bin/k3s agent --flannel-iface=tailscale0 > /tmp/k3s-debug.log 2>&1 &
pid=$!
sleep 5
sudo kill $pid
