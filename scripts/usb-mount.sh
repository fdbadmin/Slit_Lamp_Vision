#!/bin/bash
# USB automount script for SlitCam
# Strategy: Mount each USB device to /media/usb-DISKNAME, then symlink /media/usb to it.
# This avoids stale mount issues since each device gets its own mount point.

SYMLINK="/media/usb"
LOG_TAG="usb-mount"

log() {
    logger -t "$LOG_TAG" "$1"
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

do_mount() {
    sleep 2
    
    DEVICE=$(find_usb_partition)
    if [ -z "$DEVICE" ]; then
        log "No USB partition found"
        exit 1
    fi
    
    DEVNAME=$(basename "$DEVICE")
    MOUNT_POINT="/media/usb-$DEVNAME"
    
    log "Found USB: $DEVICE, mounting to $MOUNT_POINT"
    
    mkdir -p "$MOUNT_POINT"
    
    # Check if already properly mounted
    if mountpoint -q "$MOUNT_POINT" && ls "$MOUNT_POINT"/* >/dev/null 2>&1; then
        log "$DEVICE already mounted at $MOUNT_POINT"
    else
        FSTYPE=$(blkid -o value -s TYPE "$DEVICE")
        case "$FSTYPE" in
            vfat|exfat)
                mount -t "$FSTYPE" -o uid=1000,gid=1000,umask=002,noatime "$DEVICE" "$MOUNT_POINT" 2>&1 | logger -t "$LOG_TAG"
                ;;
            *)
                mount -o noatime "$DEVICE" "$MOUNT_POINT" 2>&1 | logger -t "$LOG_TAG"
                ;;
        esac
    fi
    
    # Verify mount by checking we can list files
    if mountpoint -q "$MOUNT_POINT" && ls "$MOUNT_POINT" >/dev/null 2>&1; then
        log "Mounted $DEVICE at $MOUNT_POINT"
        
        # Update symlink
        rm -f "$SYMLINK"
        ln -sf "$MOUNT_POINT" "$SYMLINK"
        log "Symlink $SYMLINK -> $MOUNT_POINT"
        
        mkdir -p "$MOUNT_POINT/slitlamp_recordings"
        chown 1000:1000 "$MOUNT_POINT/slitlamp_recordings" 2>/dev/null
        
        systemctl restart slitcam-recorder.service 2>/dev/null || true
    else
        log "Failed to mount $DEVICE"
    fi
}

case "$1" in
    mount) do_mount ;;
    *) echo "Usage: $0 mount"; exit 1 ;;
esac
