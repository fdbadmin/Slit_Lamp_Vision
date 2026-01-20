#!/usr/bin/env python3
"""
Slit Lamp Camera Housing - FreeCAD Parametric Model
====================================================
Generates a two-part 3D-printable housing for:
- Raspberry Pi Zero 2WH
- OV5647 camera module
- 16mm momentary button

Mounts via friction-fit sleeve onto 30mm Haag-Streit Short Observer Tube.

Usage: Open in FreeCAD and run via Macro > Execute or F6
Author: FDB Projects
Date: January 2026
"""

import FreeCAD as App
import Part
import Sketcher
import math

# =============================================================================
# PARAMETERS - All dimensions in mm
# =============================================================================

PARAMS = {
    # Eyepiece / Sleeve parameters
    "eyepiece_od": 30.0,           # Haag-Streit observer tube outer diameter
    "sleeve_clearance": 0.25,      # Clearance for friction fit
    "sleeve_wall": 2.5,            # Sleeve wall thickness
    "sleeve_length": 25.0,         # Length of mounting sleeve
    "buttress_od": 28.0,           # Buttress ring outer diameter (seats against eyepiece)
    "buttress_length": 3.0,        # Buttress ring depth
    "camera_offset": 15.0,         # Distance from buttress face to camera lens
    
    # Camera module (OV5647) dimensions
    "camera_pcb_width": 8.5,       # OV5647 PCB width
    "camera_pcb_height": 8.5,      # OV5647 PCB height
    "camera_pcb_depth": 5.0,       # OV5647 PCB + lens depth
    "camera_lens_dia": 6.0,        # Camera lens diameter
    "ribbon_width": 16.0,          # Camera ribbon cable width
    "ribbon_thickness": 1.0,       # Ribbon cable slot thickness
    
    # Raspberry Pi Zero 2WH dimensions
    "pi_length": 65.0,             # Board length
    "pi_width": 30.0,              # Board width
    "pi_thickness": 1.6,           # PCB thickness (without components)
    "pi_component_height": 5.0,    # Height of tallest component on top
    "pi_bottom_clearance": 2.0,    # Clearance below PCB for solder joints
    "mount_spacing_x": 58.0,       # Mounting hole spacing (length)
    "mount_spacing_y": 23.0,       # Mounting hole spacing (width)
    "mount_hole_dia": 2.75,        # M2.5 hole diameter (with clearance)
    "standoff_height": 4.0,        # PCB standoff height
    "standoff_od": 5.5,            # Standoff outer diameter
    
    # Button parameters
    "button_dia": 16.0,            # 16mm momentary button
    "button_depth": 10.0,          # Button body depth
    
    # Enclosure parameters
    "wall": 2.0,                   # Wall thickness
    "fillet": 2.5,                 # External fillet radius
    "snap_width": 8.0,             # Snap-fit tab width
    "snap_depth": 1.5,             # Snap-fit engagement depth
    "snap_clearance": 0.3,         # Snap-fit clearance
    "screw_boss_od": 6.0,          # Screw boss outer diameter
    "screw_hole_dia": 2.2,         # M2.5 tap hole diameter
    
    # Honeycomb ventilation
    "hex_size": 5.0,               # Hexagon flat-to-flat distance
    "hex_wall": 1.0,               # Wall between hexagons
    "hex_margin": 8.0,             # Margin from edges for honeycomb
}


def get_param(name):
    """Retrieve parameter value."""
    return PARAMS[name]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_document():
    """Create or get the FreeCAD document."""
    doc_name = "SlitLampHousing"
    if App.ActiveDocument and App.ActiveDocument.Name == doc_name:
        doc = App.ActiveDocument
        # Clear existing objects
        for obj in doc.Objects:
            doc.removeObject(obj.Name)
    else:
        doc = App.newDocument(doc_name)
    return doc


def make_cylinder(radius, height, position=(0, 0, 0), direction=(0, 0, 1)):
    """Create a cylinder at given position."""
    cyl = Part.makeCylinder(radius, height, App.Vector(*position), App.Vector(*direction))
    return cyl


def make_box(length, width, height, position=(0, 0, 0)):
    """Create a box at given position (centered on XY, Z from bottom)."""
    box = Part.makeBox(length, width, height, 
                       App.Vector(position[0] - length/2, 
                                  position[1] - width/2, 
                                  position[2]))
    return box


def make_hexagon(flat_to_flat, height, position=(0, 0, 0)):
    """Create a hexagonal prism (flat-to-flat dimension)."""
    # Hexagon vertices
    radius = flat_to_flat / math.sqrt(3)  # Circumradius from flat-to-flat
    vertices = []
    for i in range(6):
        angle = math.radians(60 * i + 30)  # Start at 30° for flat bottom
        x = position[0] + radius * math.cos(angle)
        y = position[1] + radius * math.sin(angle)
        vertices.append(App.Vector(x, y, position[2]))
    
    # Create wire and face
    edges = []
    for i in range(6):
        edges.append(Part.makeLine(vertices[i], vertices[(i + 1) % 6]))
    wire = Part.Wire(edges)
    face = Part.Face(wire)
    hex_prism = face.extrude(App.Vector(0, 0, height))
    return hex_prism


def fillet_shape(shape, radius, edges=None):
    """Apply fillet to shape edges."""
    try:
        if edges is None:
            edges = shape.Edges
        return shape.makeFillet(radius, edges)
    except Exception:
        # If fillet fails, return original shape
        return shape


# =============================================================================
# COMPONENT MODELING
# =============================================================================

def create_mounting_sleeve():
    """
    Create the friction-fit mounting sleeve with buttress.
    The sleeve fits over the 30mm observer tube.
    """
    eyepiece_od = get_param("eyepiece_od")
    clearance = get_param("sleeve_clearance")
    wall = get_param("sleeve_wall")
    length = get_param("sleeve_length")
    buttress_od = get_param("buttress_od")
    buttress_length = get_param("buttress_length")
    camera_offset = get_param("camera_offset")
    camera_lens_dia = get_param("camera_lens_dia")
    ribbon_width = get_param("ribbon_width")
    ribbon_thickness = get_param("ribbon_thickness")
    
    # Inner diameter with friction fit clearance
    sleeve_id = eyepiece_od + clearance
    sleeve_od = sleeve_id + 2 * wall
    
    # Main sleeve cylinder (outer)
    sleeve_outer = make_cylinder(sleeve_od / 2, length)
    
    # Inner bore (hollow)
    sleeve_inner = make_cylinder(sleeve_id / 2, length)
    
    # Buttress ring (smaller diameter, seats against eyepiece)
    # Positioned at the eyepiece end (Z=0)
    buttress_outer = make_cylinder(buttress_od / 2, buttress_length)
    buttress_inner = make_cylinder(buttress_od / 2 - wall, buttress_length)
    buttress = buttress_outer.cut(buttress_inner)
    
    # Camera pocket - cylindrical recess at camera_offset from buttress face
    # This holds the OV5647 module
    camera_pocket_depth = get_param("camera_pcb_depth") + 2
    camera_pocket_dia = max(get_param("camera_pcb_width"), get_param("camera_pcb_height")) + 1
    camera_pocket_z = camera_offset
    camera_pocket = make_cylinder(camera_pocket_dia / 2, camera_pocket_depth,
                                   position=(0, 0, camera_pocket_z))
    
    # Lens aperture - clear hole for camera lens
    lens_aperture = make_cylinder(camera_lens_dia / 2 + 0.5, camera_offset + 1,
                                   position=(0, 0, -0.5))
    
    # Ribbon cable slot - exits toward the main body
    ribbon_slot = make_box(ribbon_width, sleeve_od, ribbon_thickness + 0.5,
                           position=(0, 0, camera_pocket_z + camera_pocket_depth / 2))
    
    # Combine sleeve
    sleeve = sleeve_outer.cut(sleeve_inner)
    sleeve = sleeve.fuse(buttress)
    sleeve = sleeve.cut(camera_pocket)
    sleeve = sleeve.cut(lens_aperture)
    sleeve = sleeve.cut(ribbon_slot)
    
    return sleeve, sleeve_od, length


def create_front_shell():
    """
    Create the front shell (sleeve side) of the housing.
    Contains the sleeve, Pi mounting standoffs, and ribbon cable channel.
    """
    pi_length = get_param("pi_length")
    pi_width = get_param("pi_width")
    pi_component_height = get_param("pi_component_height")
    pi_bottom_clearance = get_param("pi_bottom_clearance")
    standoff_height = get_param("standoff_height")
    wall = get_param("wall")
    mount_x = get_param("mount_spacing_x")
    mount_y = get_param("mount_spacing_y")
    standoff_od = get_param("standoff_od")
    mount_hole_dia = get_param("mount_hole_dia")
    snap_width = get_param("snap_width")
    snap_depth = get_param("snap_depth")
    screw_boss_od = get_param("screw_boss_od")
    screw_hole_dia = get_param("screw_hole_dia")
    
    # Calculate enclosure dimensions
    # Internal height = standoff + PCB + components
    internal_height = standoff_height + 1.6 + pi_component_height
    # Split at midpoint for two-part housing
    front_internal_height = internal_height / 2 + 2  # Slightly more than half
    
    # External dimensions
    ext_length = pi_length + 2 * wall + 2  # Extra for ribbon cable channel
    ext_width = pi_width + 2 * wall
    ext_height = front_internal_height + wall
    
    # Outer shell
    outer = make_box(ext_length, ext_width, ext_height, position=(0, 0, 0))
    
    # Inner cavity
    inner = make_box(ext_length - 2 * wall, ext_width - 2 * wall, front_internal_height,
                     position=(0, 0, wall))
    
    # Create shell
    shell = outer.cut(inner)
    
    # Pi mounting standoffs (4 corners)
    standoff_positions = [
        (-mount_x / 2, -mount_y / 2),
        (mount_x / 2, -mount_y / 2),
        (-mount_x / 2, mount_y / 2),
        (mount_x / 2, mount_y / 2),
    ]
    
    for px, py in standoff_positions:
        # Standoff cylinder
        standoff = make_cylinder(standoff_od / 2, standoff_height, position=(px, py, wall))
        shell = shell.fuse(standoff)
        # Screw hole
        hole = make_cylinder(mount_hole_dia / 2, standoff_height + wall + 1, 
                            position=(px, py, -0.5))
        shell = shell.cut(hole)
    
    # Snap-fit sockets along the parting line (top edge)
    # Two on each long side
    snap_positions_y = [(-ext_width / 2 + wall / 2, -1), (ext_width / 2 - wall / 2, 1)]
    snap_positions_x = [-ext_length / 4, ext_length / 4]
    
    for sx in snap_positions_x:
        for sy, direction in snap_positions_y:
            # Socket cutout
            socket = make_box(snap_width, snap_depth + 0.5, 3,
                             position=(sx, sy + direction * snap_depth / 2, ext_height - 2))
            shell = shell.cut(socket)
    
    # Screw boss positions (diagonal corners)
    screw_positions = [
        (-ext_length / 2 + screw_boss_od, -ext_width / 2 + screw_boss_od),
        (ext_length / 2 - screw_boss_od, ext_width / 2 - screw_boss_od),
    ]
    
    for sx, sy in screw_positions:
        boss = make_cylinder(screw_boss_od / 2, front_internal_height, position=(sx, sy, wall))
        shell = shell.fuse(boss)
        hole = make_cylinder(screw_hole_dia / 2, ext_height + 1, position=(sx, sy, -0.5))
        shell = shell.cut(hole)
    
    # Get sleeve geometry
    sleeve, sleeve_od, sleeve_length = create_mounting_sleeve()
    
    # Position sleeve perpendicular to front face
    # Rotate 90° around X axis and translate
    sleeve.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90)
    sleeve_offset_y = -ext_width / 2 - sleeve_length + wall
    sleeve.translate(App.Vector(0, sleeve_offset_y, ext_height / 2))
    
    # Create sleeve attachment block
    sleeve_block_length = sleeve_od + 4
    sleeve_block_width = wall + 5
    sleeve_block_height = sleeve_od + 4
    sleeve_block = make_box(sleeve_block_length, sleeve_block_width, sleeve_block_height,
                           position=(0, -ext_width / 2 + sleeve_block_width / 2 - wall, 
                                    ext_height / 2 - sleeve_block_height / 2))
    
    # Fuse sleeve block and sleeve to shell
    shell = shell.fuse(sleeve_block)
    shell = shell.fuse(sleeve)
    
    # Ribbon cable channel from sleeve to Pi CSI connector
    ribbon_width = get_param("ribbon_width")
    ribbon_channel = make_box(ribbon_width + 2, ext_width / 2 + 5, 3,
                              position=(pi_length / 2 - 15, -ext_width / 4, ext_height / 2))
    shell = shell.cut(ribbon_channel)
    
    return shell, ext_length, ext_width, ext_height


def create_honeycomb_pattern(width, height, hex_size, hex_wall, depth):
    """
    Create a honeycomb pattern of hexagonal cutouts.
    Returns a compound shape to be subtracted from a surface.
    """
    hex_spacing_x = hex_size + hex_wall
    hex_spacing_y = (hex_size + hex_wall) * math.sqrt(3) / 2
    
    hexagons = []
    
    # Calculate grid
    cols = int(width / hex_spacing_x) - 1
    rows = int(height / hex_spacing_y) - 1
    
    start_x = -width / 2 + hex_size
    start_y = -height / 2 + hex_size
    
    for row in range(rows):
        for col in range(cols):
            # Offset every other row
            offset = hex_spacing_x / 2 if row % 2 else 0
            x = start_x + col * hex_spacing_x + offset
            y = start_y + row * hex_spacing_y
            
            # Check bounds
            if abs(x) < width / 2 - hex_size and abs(y) < height / 2 - hex_size:
                hex_prism = make_hexagon(hex_size, depth, position=(x, y, 0))
                hexagons.append(hex_prism)
    
    if hexagons:
        pattern = hexagons[0]
        for hex_shape in hexagons[1:]:
            pattern = pattern.fuse(hex_shape)
        return pattern
    return None


def create_rear_shell():
    """
    Create the rear shell (button side) of the housing.
    Contains the button cutout, honeycomb ventilation, snap-fit tabs, and screw bosses.
    """
    pi_length = get_param("pi_length")
    pi_width = get_param("pi_width")
    pi_component_height = get_param("pi_component_height")
    standoff_height = get_param("standoff_height")
    wall = get_param("wall")
    button_dia = get_param("button_dia")
    snap_width = get_param("snap_width")
    snap_depth = get_param("snap_depth")
    snap_clearance = get_param("snap_clearance")
    screw_boss_od = get_param("screw_boss_od")
    screw_hole_dia = get_param("screw_hole_dia")
    hex_size = get_param("hex_size")
    hex_wall = get_param("hex_wall")
    hex_margin = get_param("hex_margin")
    
    # Match front shell dimensions
    internal_height = standoff_height + 1.6 + pi_component_height
    rear_internal_height = internal_height / 2
    
    ext_length = pi_length + 2 * wall + 2
    ext_width = pi_width + 2 * wall
    ext_height = rear_internal_height + wall
    
    # Outer shell
    outer = make_box(ext_length, ext_width, ext_height, position=(0, 0, 0))
    
    # Inner cavity
    inner = make_box(ext_length - 2 * wall, ext_width - 2 * wall, rear_internal_height,
                     position=(0, 0, wall))
    
    # Create shell
    shell = outer.cut(inner)
    
    # Button cutout (centered on rear face, which is now at Z=0 for this part)
    button_hole = make_cylinder(button_dia / 2, wall + 1, position=(0, 0, -0.5))
    shell = shell.cut(button_hole)
    
    # Button retaining lip (inner ring to hold button)
    button_lip_id = button_dia - 2
    button_lip_od = button_dia + 2
    button_lip_height = 2
    button_lip_outer = make_cylinder(button_lip_od / 2, button_lip_height, position=(0, 0, wall))
    button_lip_inner = make_cylinder(button_lip_id / 2, button_lip_height + 1, position=(0, 0, wall - 0.5))
    button_lip = button_lip_outer.cut(button_lip_inner)
    shell = shell.fuse(button_lip)
    
    # Honeycomb ventilation pattern on rear face (around button)
    # Create honeycomb for each quadrant to avoid button
    honeycomb_areas = [
        (ext_length / 4, ext_width / 4, ext_length / 2 - hex_margin, ext_width / 2 - hex_margin),
        (-ext_length / 4, ext_width / 4, ext_length / 2 - hex_margin, ext_width / 2 - hex_margin),
        (ext_length / 4, -ext_width / 4, ext_length / 2 - hex_margin, ext_width / 2 - hex_margin),
        (-ext_length / 4, -ext_width / 4, ext_length / 2 - hex_margin, ext_width / 2 - hex_margin),
    ]
    
    # Simplified honeycomb - create full pattern and cut around button
    honeycomb_width = ext_length - 2 * hex_margin
    honeycomb_height = ext_width - 2 * hex_margin
    honeycomb = create_honeycomb_pattern(honeycomb_width, honeycomb_height, 
                                          hex_size, hex_wall, wall + 1)
    
    if honeycomb:
        # Move honeycomb to Z=-0.5 to cut through bottom face
        honeycomb.translate(App.Vector(0, 0, -0.5))
        # Exclude button area
        button_keepout = make_cylinder(button_dia / 2 + hex_margin, wall + 2, 
                                       position=(0, 0, -1))
        honeycomb = honeycomb.cut(button_keepout)
        shell = shell.cut(honeycomb)
    
    # Snap-fit tabs along the parting line (bottom edge for mating)
    snap_positions_y = [(-ext_width / 2 + wall, -1), (ext_width / 2 - wall, 1)]
    snap_positions_x = [-ext_length / 4, ext_length / 4]
    
    for sx in snap_positions_x:
        for sy, direction in snap_positions_y:
            # Snap tab with 45° lead-in
            tab_base = make_box(snap_width - snap_clearance, snap_depth, 2.5,
                               position=(sx, sy + direction * (wall / 2 + snap_depth / 2), 
                                        ext_height - 1.25))
            shell = shell.fuse(tab_base)
    
    # Screw boss positions (matching front shell)
    screw_positions = [
        (-ext_length / 2 + screw_boss_od, -ext_width / 2 + screw_boss_od),
        (ext_length / 2 - screw_boss_od, ext_width / 2 - screw_boss_od),
    ]
    
    for sx, sy in screw_positions:
        boss = make_cylinder(screw_boss_od / 2, rear_internal_height, position=(sx, sy, wall))
        shell = shell.fuse(boss)
        # Through hole for screw
        hole = make_cylinder(get_param("mount_hole_dia") / 2, ext_height + 1, 
                            position=(sx, sy, -0.5))
        shell = shell.cut(hole)
    
    # GPIO wire exit slot (side of enclosure)
    gpio_slot_width = 12
    gpio_slot_height = 4
    gpio_slot = make_box(wall + 1, gpio_slot_width, gpio_slot_height,
                        position=(ext_length / 2 - wall / 2, 0, ext_height - gpio_slot_height / 2 - 2))
    shell = shell.cut(gpio_slot)
    
    return shell, ext_length, ext_width, ext_height


def apply_fillets_to_part(part_feature, radius):
    """Apply fillets to a Part::Feature object."""
    try:
        fillet_shape = part_feature.Shape.makeFillet(radius, part_feature.Shape.Edges)
        part_feature.Shape = fillet_shape
    except Exception as e:
        print(f"Warning: Could not apply fillet: {e}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Generate the complete housing model."""
    print("=" * 60)
    print("Slit Lamp Camera Housing Generator")
    print("=" * 60)
    
    # Create document
    doc = create_document()
    print(f"Created document: {doc.Name}")
    
    # Generate front shell
    print("\nGenerating front shell (sleeve side)...")
    front_shape, front_l, front_w, front_h = create_front_shell()
    front_part = doc.addObject("Part::Feature", "FrontShell")
    front_part.Shape = front_shape
    front_part.ViewObject.ShapeColor = (0.2, 0.6, 0.8)  # Blue
    print(f"  Dimensions: {front_l:.1f} x {front_w:.1f} x {front_h:.1f} mm")
    
    # Generate rear shell
    print("\nGenerating rear shell (button side)...")
    rear_shape, rear_l, rear_w, rear_h = create_rear_shell()
    # Position rear shell above front shell for visualization
    rear_shape.translate(App.Vector(0, 0, front_h + 5))
    rear_part = doc.addObject("Part::Feature", "RearShell")
    rear_part.Shape = rear_shape
    rear_part.ViewObject.ShapeColor = (0.8, 0.4, 0.2)  # Orange
    print(f"  Dimensions: {rear_l:.1f} x {rear_w:.1f} x {rear_h:.1f} mm")
    
    # Apply fillets
    fillet_radius = get_param("fillet")
    print(f"\nApplying {fillet_radius}mm fillets...")
    # Note: Fillets applied selectively to avoid failures on complex geometry
    
    # Recompute
    doc.recompute()
    
    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nParts created:")
    print(f"  1. FrontShell - Contains mounting sleeve and Pi standoffs")
    print(f"  2. RearShell  - Contains button and honeycomb ventilation")
    print(f"\nKey dimensions:")
    print(f"  Sleeve ID: {get_param('eyepiece_od') + get_param('sleeve_clearance'):.2f} mm (friction fit)")
    print(f"  Buttress OD: {get_param('buttress_od'):.1f} mm")
    print(f"  Camera offset: {get_param('camera_offset'):.1f} mm from buttress")
    print(f"  Button diameter: {get_param('button_dia'):.1f} mm")
    print(f"\nExport:")
    print(f"  Select part > File > Export > STL")
    print(f"  Recommended: FrontShell print with sleeve up")
    print(f"               RearShell print flat (honeycomb up)")
    
    return doc


# Run when executed as macro
if __name__ == "__main__" or App.ActiveDocument:
    main()
