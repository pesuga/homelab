#!/bin/bash

# WARNING: This script forcefully removes Kubernetes namespaces and ALL resources
# within them, including PersistentVolumeClaims (PVCs).
# EXECUTING THIS SCRIPT WILL RESULT IN PERMANENT DATA LOSS FOR THE TARGET APPLICATIONS.
# Ensure you have backed up any necessary data before running this script.
# This script is intended for the initial cleanup of deprecated applications.

set -e # Exit immediately if a command exits with a non-zero status.

echo "Attempting to delete deprecated application namespaces..."

# List of namespaces associated with the applications being removed
# Adjust these names if the actual namespaces differ.
namespaces=(
    "glance"
    "jellyfin"
    "home-assistant"
    "immich"
    "owncloud"
)

for ns in "${namespaces[@]}"; do
    echo "--- Deleting namespace: $ns ---"
    # Use --ignore-not-found to avoid errors if a namespace was already deleted or never existed.
    # Use --force and --grace-period=0 for faster deletion, potentially bypassing finalizers.
    # Be cautious with --force, as it can leave orphaned resources in some edge cases.
    kubectl delete namespace "$ns" --ignore-not-found=true --force --grace-period=0 || echo "Failed to delete namespace $ns or it didn't exist."
    echo "--- Namespace $ns deletion command issued. ---"
    # Note: Namespace deletion can take time in the background.
done

echo "Deprecated application namespace deletion commands issued."
echo "Monitor 'kubectl get ns' to confirm deletion completion."
echo "WARNING: Data associated with PVCs in these namespaces has been deleted."
