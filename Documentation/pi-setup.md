# Raspberry Pi setup (Pi OS Lite 64-bit, Pi Zero 2 W)

Target: Raspberry Pi OS Lite 64-bit (Bookworm) flashed with Raspberry Pi Imager.

## Imager settings (recommended)

- Set hostname (e.g., `slitlamp`)
- Enable SSH
- Configure username/password (`pi`)
- Add your SSH public key
- Configure Wi‑Fi

## First boot

```bash
sudo apt update
sudo apt upgrade -y
```

## Camera

Install libcamera apps:

```bash
sudo apt install -y libcamera-apps
```

Verify the camera is detected:

```bash
libcamera-vid --list-cameras
```

## GPIO permissions (run as `pi`)

Install gpiozero:

```bash
sudo apt install -y python3-gpiozero
```

Add user `pi` to the gpio group:

```bash
sudo usermod -aG gpio pi
# then reboot (or log out/in) so group membership applies
sudo reboot
```

## USB filesystems (Windows-friendly)

We support USB sticks formatted as:
- exFAT (recommended)
- FAT32

Install tooling:

```bash
sudo apt install -y exfatprogs dosfstools
```

Optional NTFS (best-effort):

```bash
sudo apt install -y ntfs-3g
```
