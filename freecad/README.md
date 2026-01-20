# Slit Lamp Camera Housing - FreeCAD Design

## Overview

This FreeCAD project generates a two-part 3D-printable housing for the slit lamp camera system. The housing mounts via friction-fit sleeve onto a 30mm Haag-Streit Short Observer Tube (BQ900).

## Components Housed

| Component | Model | Dimensions |
|-----------|-------|------------|
| Main board | Raspberry Pi Zero 2WH | 65 × 30 × ~12mm (with GPIO) |
| Camera | OV5647 module | 8.5 × 8.5 × 5mm |
| Button | 16mm momentary | Ø16 × ~10mm |

## Design Files

| File | Description |
|------|-------------|
| `slit_lamp_housing.py` | Main parametric model generator script |
| `slit_lamp_housing.FCStd` | FreeCAD native file (generated) |
| `FrontShell.stl` | Front half STL export (generated) |
| `RearShell.stl` | Rear half STL export (generated) |

## Usage

### In FreeCAD

1. Open FreeCAD (tested with v0.21+)
2. **Macro** → **Macros...** → Browse to `slit_lamp_housing.py`
3. Click **Execute**
4. Two parts will be generated: `FrontShell` and `RearShell`

### Modifying Parameters

Edit the `PARAMS` dictionary at the top of `slit_lamp_housing.py`:

```python
PARAMS = {
    "eyepiece_od": 30.0,        # Change this for different slit lamps
    "sleeve_clearance": 0.25,   # Adjust for tighter/looser fit
    # ... etc
}
```

### Exporting STL

1. Select part in Model tree (e.g., `FrontShell`)
2. **File** → **Export...**
3. Choose **STL Mesh** format
4. Save as `FrontShell.stl`
5. Repeat for `RearShell`

## Parameter Reference

### Eyepiece / Sleeve Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `eyepiece_od` | 30.0 mm | Haag-Streit observer tube outer diameter |
| `sleeve_clearance` | 0.25 mm | Clearance for friction fit (increase if too tight) |
| `sleeve_wall` | 2.5 mm | Sleeve wall thickness |
| `sleeve_length` | 25.0 mm | Length of mounting sleeve |
| `buttress_od` | 28.0 mm | Buttress ring OD (seats against eyepiece) |
| `buttress_length` | 3.0 mm | Buttress ring depth |
| `camera_offset` | 15.0 mm | Distance from buttress face to camera lens |

### Camera Module (OV5647)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `camera_pcb_width` | 8.5 mm | OV5647 PCB width |
| `camera_pcb_height` | 8.5 mm | OV5647 PCB height |
| `camera_pcb_depth` | 5.0 mm | OV5647 PCB + lens depth |
| `camera_lens_dia` | 6.0 mm | Camera lens diameter |
| `ribbon_width` | 16.0 mm | Camera ribbon cable width |
| `ribbon_thickness` | 1.0 mm | Ribbon cable slot thickness |

### Raspberry Pi Zero 2WH

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pi_length` | 65.0 mm | Board length |
| `pi_width` | 30.0 mm | Board width |
| `pi_thickness` | 1.6 mm | PCB thickness |
| `pi_component_height` | 5.0 mm | Height of tallest component |
| `pi_bottom_clearance` | 2.0 mm | Clearance below PCB |
| `mount_spacing_x` | 58.0 mm | Mounting hole spacing (length) |
| `mount_spacing_y` | 23.0 mm | Mounting hole spacing (width) |
| `mount_hole_dia` | 2.75 mm | M2.5 hole diameter |
| `standoff_height` | 4.0 mm | PCB standoff height |
| `standoff_od` | 5.5 mm | Standoff outer diameter |

### Button

| Parameter | Default | Description |
|-----------|---------|-------------|
| `button_dia` | 16.0 mm | Button diameter |
| `button_depth` | 10.0 mm | Button body depth |

### Enclosure

| Parameter | Default | Description |
|-----------|---------|-------------|
| `wall` | 2.0 mm | Wall thickness |
| `fillet` | 2.5 mm | External fillet radius |
| `snap_width` | 8.0 mm | Snap-fit tab width |
| `snap_depth` | 1.5 mm | Snap-fit engagement depth |
| `snap_clearance` | 0.3 mm | Snap-fit clearance |
| `screw_boss_od` | 6.0 mm | Screw boss outer diameter |
| `screw_hole_dia` | 2.2 mm | M2.5 tap hole diameter |

### Honeycomb Ventilation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `hex_size` | 5.0 mm | Hexagon flat-to-flat distance |
| `hex_wall` | 1.0 mm | Wall between hexagons |
| `hex_margin` | 8.0 mm | Margin from edges |

## Assembly

### Two-Part Housing Assembly

The housing consists of two shells that mate together:

1. **FrontShell** (sleeve side)
   - Contains friction-fit mounting sleeve
   - Pi Zero mounting standoffs (4× M2.5)
   - Ribbon cable channel
   - Snap-fit sockets

2. **RearShell** (button side)
   - 16mm button cutout with retaining lip
   - Honeycomb ventilation pattern
   - Snap-fit tabs
   - GPIO wire exit slot

### Assembly Method

1. Mount Pi Zero 2WH to FrontShell standoffs using 4× M2.5×6mm screws
2. Connect camera ribbon cable through channel
3. Route GPIO wires to button
4. Snap RearShell onto FrontShell (tabs engage in sockets)
5. Secure with 2× M2.5×12mm screws at diagonal corners

### Hardware Required

| Item | Quantity | Notes |
|------|----------|-------|
| M2.5 × 6mm pan head screws | 4 | Pi mounting |
| M2.5 × 12mm pan head screws | 2 | Shell assembly |
| M2.5 heat-set inserts (optional) | 2 | For screw bosses |

## 3D Printing

### Recommended Settings

| Setting | FrontShell | RearShell |
|---------|------------|-----------|
| **Orientation** | Sleeve up (vertical) | Flat (honeycomb up) |
| **Layer height** | 0.2 mm | 0.2 mm |
| **Infill** | 20% | 20% |
| **Supports** | Yes (sleeve interior) | No |
| **Material** | PLA or PETG | PLA or PETG |

### Printer: Bambu Lab A1

Recommended profile:
- Standard quality (0.20mm)
- Tree supports for FrontShell
- Enable bridge detection

### Fit Adjustments

If the sleeve is too tight:
- Increase `sleeve_clearance` by 0.1mm increments

If snap-fits are too loose:
- Decrease `snap_clearance` by 0.1mm

If snap-fits are too tight:
- Increase `snap_clearance` by 0.1mm

## Design Rationale

### DSLR-Style Form Factor

The housing mimics a conventional camera body with lens:
- Main body (rectangular prism) = Pi enclosure
- "Lens barrel" = Mounting sleeve
- This orientation places controls accessible during use

### Friction-Fit Sleeve

- Allows tool-free attachment/removal
- Buttress ring ensures consistent positioning
- 0.25mm clearance balances grip vs. ease of removal

### Low-Profile Design

- Minimal internal clearances
- No wasted space
- Reduces weight on eyepiece

### Rounded Edges

- 2.5mm fillets on all external edges
- Comfortable handling
- Professional appearance

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-20 | Initial parametric design |

## License

This design is part of the FDB Projects Slit Lamp Camera system.
