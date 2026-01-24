#!/bin/bash
# USB automount script for SlitCam
# Strategy: Clean up stale mounts, then mount USB to /media/usb-DISKNAME with symlink.
# Includes cleanup of stale mounts and retry logic for reliable hotplug.

SYMLINK="/media/usb"
LOG_TAG="usb-mount"
MAX_RETRIES=5
RETRY_DELAY=2

log() {
    logger -t "$LOG_TAG" "$1"
}

# Clean up all stale/dead USB mounts (devices that no longer exist)
cleanup_stale_mounts() {
    log "Cleaning up stale USB mounts..."
    
    # First, remove stale symlink
    if [ -L "$SYMLINK" ]; then
        local target=$(readlink -f "$SYMLINK" 2>/dev/null)
        if [ ! -d "$target" ] || ! mountpoint -q "$target" 2>/dev/null; then
            log "Removing stale symlink $SYMLINK"
            rm -f "$SYMLINK"
        fi
    fi
    
    # Clean up all /media/usb-sd* mount points
    for mnt in /media/usb-sd*; do
        [ -d "$mnt" ] || continue
        # Extract device from mount point name
        devname=$(basename "$mnt" | sed 's/usb-//')
        device="/dev/$devname"
        
        # If device no longer exists, unmount and remove
        if ! [ -b "$device" ]; then
            log "Device $device gone, cleaning up $mnt"
            umount -l "$mnt" 2>/dev/null
            sleep 0.5
            rmdir "$mnt" 2>/dev/null
        elif mountpoint -q "$mnt" && ! ls "$mnt" >/dev/null 2>&1; then
            # Mount exists but is stale/inaccessible
            log "Mount $mnt is stale, cleaning up"
            umount -l "$mnt" 2>/dev/null
            sleep 0.5
            rmdir "$mnt" 2>/dev/null
        fi
    done
}

# Find the first USB block device with a filesystem
find_usb_partition() {
    for disk in /sys/block/sd*; do
        [ -d "$disk" ] || continue
        if readlink -f "$disk/device" | grep -q usb; then
            DISKNAME=$(basename "$disk")
            PART="/dev/${DISKNAME}1"
            if [ -b "$PART" ] && blkid -o value -s TYPE "$PART" >/dev/null 2>&1; then
                echo "$PART"
                return 0
            fi
        fi
    done
    return 1
}

try_mount() {
    local DEVICE="$1"
    local MOUNT_POINT="$2"
    
    FSTYPE=$(blkid -o value -s TYPE "$DEVICE" 2>/dev/null)
    case "$FSTYPE" in
        vfat|exfat)
            mount -t "$FSTYPE" -o uid=1000,gid=1000,umask=002,noatime "$DEVICE" "$MOUNT_POINT" 2>&1
            ;;
        *)
            mount -o noatime "$DEVICE" "$MOUNT_POINT" 2>&1
            ;;
    esac
}

do_mount() {
    # Clean up all stale mounts first
    cleanup_stale_mounts
    
    # Longer initial delay for device to settle after hotplug
    log "Waiting for device to settle..."
    sleep 3
    
    # Retry loop to find and mount USB
    for attempt in $(seq 1 $MAX_RETRIES); do
        log "Mount attempt $attempt of $MAX_RETRIES"
        
        DEVICE=$(find_usb_partition)
        if [ -z "$DEVICE" ]; then
            log "No USB partition found, retrying..."
            sleep $RETRY_DELAY
            continue
        fi
        
        DEVNAME=$(basename "$DEVICE")
        MOUNT_POINT="/media/usb-$DEVNAME"
        
        log "Found USB: $DEVICE, mounting to $MOUNT_POINT"
        mkdir -p "$MOUNT_POINT"
        
        # If mount point is already in use by something stale, force unmount
        if mountpoint -q "$MOUNT_POINT"; then
            if ! ls "$MOUNT_POINT" >/dev/null 2>&1; then
                log "Stale mount at $MOUNT_POINT, unmounting..."
                umount -l "$MOUNT_POINT" 2>/dev/null
                sleep 1
            fi
        fi
        
        # Check if already properly mounted
        if mountpoint -q "$MOUNT_POINT" && ls "$MOUNT_POINT" >/dev/null 2>&1; then
            log "$DEVICE already mounted at $MOUNT_POINT"
        else
            # Try to mount
            MOUNT_OUTPUT=$(try_mount "$DEVICE" "$MOUNT_POINT" 2>&1)
            if [ -n "$MOUNT_OUTPUT" ]; then
                log "Mount output: $MOUNT_OUTPUT"
            fi
        fi
        
        # Verify mount succeeded
        if mountpoint -q "$MOUNT_POINT" && ls "$MOUNT_POINT" >/dev/null 2>&1; then
            log "Successfully mounted $DEVICE at $MOUNT_POINT"
            
            # Update symlink
            rm -f "$SYMLINK"
            ln -sf "$MOUNT_POINT" "$SYMLINK"
            log "Symlink $SYMLINK -> $MOUNT_POINT"
            
            # Create recordings directory
            mkdir -p "$MOUNT_POINT/slitlamp_recordings"
            chown 1000:1000 "$MOUNT_POINT/slitlamp_recordings" 2>/dev/null
            
            # Restart service
            sleep 1
            systemctl restart slitcam-recorder.service 2>&1 | logger -t "$LOG_TAG"
            log "Restarted slitcam-recorder.service"
            
            exit 0
        else
            log "Mount attempt $attempt failed, retrying..."
            sleep $RETRY_DELAY
        fi
    done
    
    log "ERROR: Failed to mount USB after $MAX_RETRIES attempts"
    exit 1
}

# Unmount ALL USB drives - called on USB removal
# Device names change between plugs (sda1→sdb1), so clean up everything
do_unmount() {
    log "Unmounting all USB drives..."
    
    # Remove the symlink first
    if [ -L "$SYMLINK" ]; then
        log "Removing symlink $SYMLINK"
        rm -f "$SYMLINK"
    fi
    
    # Unmount and remove ALL /media/usb-* mount points
    for mnt in /media/usb-*; do
        [ -d "$mnt" ] || continue
        [ "$mnt" = "/media/usb" ] && continue  # skip symlink if it's a dir
        
        log "Unmounting $mnt"
        umount -l "$mnt" 2>/dev/null
        sleep 0.2
        rmdir "$mnt" 2>/dev/null
    done
    
    log "USB unmount complete"
}

case "$1" in
    mount) do_mount ;;
    unmount) do_unmount ;;
    *) echo "Usage: $0 {mount|unmount}"; exit 1 ;;
esac
