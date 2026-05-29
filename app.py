# GRADIO parametric non-planar laboratory
import math
import gradio as gr
import fullcontrol as fc

# =====================================================================
# GEOMETRY ENGINE: CYLINDER
# =====================================================================
def generate_cylinder(radius, total_height, z_amplitude, z_frequency, nozzle_diameter, layer_height, print_speed, nozzle_temp, bed_temp):
    steps = []
    base_layers = 5
    total_layers = int(total_height / layer_height)
    center_x, center_y = 128.0, 128.0
    
    # Smooth anti-chop base floor
    for l_idx in range(base_layers):
        lz = l_idx * layer_height
        ring_spacing = 0.52
        max_rings = int(radius / ring_spacing)
        for r_idx in range(max_rings + 1, 6, -1):
            r = r_idx * ring_spacing
            for seg in range(73):
                angle = (seg / 72) * 2.0 * math.pi
                steps.append(fc.Point(x=center_x + r*math.cos(angle), y=center_y + r*math.sin(angle), z=lz))
                
    # Wavy Upper Walls
    for l_idx in range(base_layers, total_layers):
        lz_base = l_idx * layer_height
        factor = min(1.0, (lz_base - 5.0) / 12.0) if lz_base > 5.0 else 0.0
        for seg in range(121):
            angle = (seg / 120) * 2.0 * math.pi
            z = lz_base + (z_amplitude * math.sin(angle * z_frequency) * factor)
            steps.append(fc.Point(x=center_x + radius*math.cos(angle), y=center_y + radius*math.sin(angle), z=z))
            
    return steps

# =====================================================================
# GEOMETRY ENGINE: VASE
# =====================================================================
def generate_vase(base_radius, total_height, twist_rate, ripple_depth, nozzle_diameter, layer_height, print_speed, nozzle_temp, bed_temp):
    steps = []
    base_layers = 5
    total_layers = int(total_height / layer_height)
    center_x, center_y = 128.0, 128.0
    
    for l_idx in range(base_layers):
        lz = l_idx * layer_height
        for r_idx in range(int(base_radius/0.52) + 1, 5, -1):
            r = r_idx * 0.52
            for seg in range(73):
                angle = (seg / 72) * 2.0 * math.pi
                steps.append(fc.Point(x=center_x + r*math.cos(angle), y=center_y + r*math.sin(angle), z=lz))
                
    for l_idx in range(base_layers, total_layers):
        lz_base = l_idx * layer_height
        helix_shift = lz_base * twist_rate
        factor = min(1.0, (lz_base - 5.0) / 15.0) if lz_base > 5.0 else 0.0
        for seg in range(145):
            angle = (seg / 144) * 2.0 * math.pi
            ripple = math.sin(angle * 12.0 + helix_shift) * ripple_depth * factor
            r = base_radius + ripple
            x = center_x + r * math.cos(angle + helix_shift)
            y = center_y + r * math.sin(angle + helix_shift)
            steps.append(fc.Point(x=x, y=y, z=lz_base))
            
    return steps

# =====================================================================
# GEOMETRY ENGINE: FIDGET
# =====================================================================
def generate_fidget(tile_size, wave_pattern, spring_amplitude, nozzle_diameter, layer_height, print_speed, nozzle_temp, bed_temp):
    steps = []
    cell_size = 8.0
    total_layers = int(12.0 / layer_height)
    center_x, center_y = 128.0, 128.0
    min_x, min_y = center_x - (tile_size/2.0), center_y - (tile_size/2.0)
    
    for l_idx in range(total_layers):
        lz = l_idx * layer_height
        factor = math.sin((lz / 12.0) * math.pi)
        for gy in range(int(tile_size / cell_size)):
            y_start = min_y + (gy * cell_size)
            for gx in range(int(tile_size / cell_size)):
                x_start = min_x + (gx * cell_size)
                for step_idx in range(11):
                    t = step_idx / 10
                    x = x_start + (t * cell_size)
                    y_bend = spring_amplitude * math.sin(x * wave_pattern + lz) * factor
                    y = y_start + (t * cell_size) + y_bend
                    z = lz + (spring_amplitude * math.cos(x * wave_pattern) * factor)
                    steps.append(fc.Point(x=x, y=y, z=z))
                    
    return steps

# =====================================================================
# MAIN ROUTINE EXPORT COMPILER
# =====================================================================
def master_compiler(model_type, size, height, var1, var2, nozzle_dia, lay_height, speed, temp_nz, temp_bd):
    if "Cylinder" in model_type:
        steps = generate_cylinder(size, height, var1, int(var2), nozzle_dia, lay_height, speed, temp_nz, temp_bd)
        out_name = "wavy_cylinder.gcode"
    elif "Vase" in model_type:
        steps = generate_vase(size, height, var1, var2, nozzle_dia, lay_height, speed, temp_nz, temp_bd)
        out_name = "twisted_vase.gcode"
    else:
        steps = generate_fidget(size, var1, var2, nozzle_dia, lay_height, speed, temp_nz, temp_bd)
        out_name = "fidget_tile.gcode"
        
    print_settings = {
        'extrusion_width': nozzle_dia + 0.04,
        'extrusion_height': lay_height,
        'print_speed': speed * 60,
        'nozzle_temp': temp_nz,
        'bed_temp': temp_bd
    }
    
    gcode = fc.transform(steps, 'gcode', fc.GcodeControls(printer_name='bambulab_x1', initialization_data=print_settings))
    gcode = gcode.replace(f"G1 F{speed * 60}", "G1 F900", 1)
    
    # Save text file locally on server to feed download port
    with open(out_name, "w") as f:
        f.write(gcode)
        
    return out_name

# --- GRADIO LAYOUT DRAWING ENVIRONMENT ---
with gr.Blocks(title="Parametric Nonplanar Lab") as demo:
    gr.Markdown("# 🌀 Open-Source Parametric Non-Planar G-Code Lab")
    gr.Markdown("Powered by **FullControl GCODE Designer**. Adjust the sliders to generate your unconstrained machine toolpaths instantly.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🖨️ 1. Printer Profile")
            nozzle_dia = gr.Dropdown([0.4, 0.6, 0.8], value=0.4, label="Nozzle Size (mm)")
            lay_height = gr.Slider(0.1, 0.4, value=0.2, step=0.05, label="Layer Height (mm)")
            speed = gr.Slider(10, 150, value=60, label="Wall Speed (mm/s)")
            temp_nz = gr.Slider(190, 270, value=240, label="Nozzle Temp (°C)")
            temp_bd = gr.Slider(40, 90, value=75, label="Bed Temp (°C)")
            
        with gr.Column():
            gr.Markdown("### ⚙️ 2. Shape Customization")
            model_type = gr.Radio(["1. Ribbon Cylinder", "2. Twisted Vase", "3. Fidget Tile"], value="1. Ribbon Cylinder", label="Select Shape")
            
            # Parametric Multi-Use Sliders
            size = gr.Slider(10.0, 100.0, value=38.1, label="Base Width/Radius (mm)")
            height = gr.Slider(10.0, 250.0, value=80.0, label="Total Object Height (mm)")
            var1 = gr.Slider(-0.1, 10.0, value=2.5, label="Modifier 1 (Wave Amp / Twist Rate / Density)")
            var2 = gr.Slider(0.0, 24.0, value=4.0, label="Modifier 2 (Wave Count / Rib Depth / Compression)")
            
    btn = gr.Button("💾 Generate & Compile G-code File", variant="primary")
    file_output = gr.File(label="Download Generated Machine Code")
    
    btn.click(
        master_compiler, 
        inputs=[model_type, size, height, var1, var2, nozzle_dia, lay_height, speed, temp_nz, temp_bd], 
        outputs=file_output
    )

demo.launch()
