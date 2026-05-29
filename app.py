import math
import streamlit as st
import fullcontrol as fc

# --- 1. CORE WEB APP HEADER & OPEN-SOURCE CREDIT ---
st.set_page_config(page_title="Parametric Non-Planar G-Code Lab", layout="wide")
st.title("🌀 Parametric Non-Planar G-Code Lab")
st.markdown("""
Welcome to the community library! This web tool generates raw, unconstrained 3D print paths mathematically.
*   **Powered by:** [FullControl GCODE Designer](https://github.com) (Full credit to Heinz-Loepmeier & FullControl contributors).
*   **Target Machine Profile:** Optimized for standard 256x256mm build plates (e.g., Bambu Lab P1S/X1/A1).
""")

# --- 2. GLOBAL SIDEBAR CONFIGURATION (PRINTER SETTINGS) ---
st.sidebar.header("🖨️ Printer Profile")
center_x = st.sidebar.number_input("Bed Center X (mm)", value=128.0)
center_y = st.sidebar.number_input("Bed Center Y (mm)", value=128.0)
nozzle_diameter = st.sidebar.selectbox("Nozzle Diameter (mm)", [0.4, 0.6, 0.8], index=0)
layer_height = st.sidebar.slider("Layer Height (mm)", 0.1, 0.4, 0.2, step=0.05)
print_speed = st.sidebar.slider("Print Speed (mm/s)", 10, 150, 60)
nozzle_temp = st.sidebar.slider("Nozzle Temp (°C)", 190, 270, 240)
bed_temp = st.sidebar.slider("Bed Temp (°C)", 40, 90, 75)

# --- 3. CHOOSE MODEL TO CUSTOMIZE ---
model_choice = st.selectbox(
    "Select a Model to Customize & Generate", 
    ["1. Non-Planar Ribbon Cylinder", "2. Twisted Wave-Mesh Vase", "3. Parametric Gyroscopic Fidget Tile"]
)

# Initialize container for FullControl vector steps
steps = []
filename = "model.gcode"

# =====================================================================
# MODEL 1: NON-PLANAR RIBBON CYLINDER WITH ANTI-CHOP SMOOTH BASE
# =====================================================================
if model_choice == "1. Non-Planar Ribbon Cylinder":
    st.subheader("⚙️ Cylinder Customization Parameters")
    col1, col2 = st.columns(2)
    with col1:
        radius = st.slider("Cylinder Radius (mm)", 10.0, 100.0, 38.1)
        total_height = st.slider("Total Height (mm)", 20.0, 200.0, 80.0)
    with col2:
        z_amplitude = st.slider("Non-Planar Wave Height (mm)", 0.0, 8.0, 2.5)
        z_frequency = st.slider("Wave Count around Perimeter", 2, 12, 4)
        
    def generate_cylinder():
        cyl_steps = []
        base_layers = 5
        total_layers = int(total_height / layer_height)
        
        # Smooth anti-chop base floor
        for l_idx in range(base_layers):
            lz = l_idx * layer_height
            ring_spacing = 0.52
            max_rings = int(radius / ring_spacing)
            for r_idx in range(max_rings + 1, 6, -1):
                r = r_idx * ring_spacing
                for seg in range(73):
                    angle = (seg / 72) * 2.0 * math.pi
                    cyl_steps.append(fc.Point(x=center_x + r*math.cos(angle), y=center_y + r*math.sin(angle), z=lz))
                    
        # Wavy Upper Walls
        for l_idx in range(base_layers, total_layers):
            lz_base = l_idx * layer_height
            factor = min(1.0, (lz_base - 5.0) / 12.0) if lz_base > 5.0 else 0.0
            for seg in range(121):
                angle = (seg / 120) * 2.0 * math.pi
                z = lz_base + (z_amplitude * math.sin(angle * z_frequency) * factor)
                cyl_steps.append(fc.Point(x=center_x + radius*math.cos(angle), y=center_y + radius*math.sin(angle), z=z))
        return cyl_steps
        
    steps = generate_cylinder()
    filename = "smooth_base_wavy_cylinder.gcode"

# =====================================================================
# MODEL 2: TWISTED WAVE-MESH VASE (ORGANIC GEOMETRIC PERIMETER)
# =====================================================================
elif model_choice == "2. Twisted Wave-Mesh Vase":
    st.subheader("⚙️ Vase Customization Parameters")
    col1, col2 = st.columns(2)
    with col1:
        base_radius = st.slider("Vase Radius (mm)", 15.0, 90.0, 40.0)
        total_height = st.slider("Vase Height (mm)", 30.0, 250.0, 100.0)
    with col2:
        twist_rate = st.slider("Spiral Twist Rate", -0.1, 0.1, 0.04, step=0.01)
        ripple_depth = st.slider("Rib Lattice Depth (mm)", 0.0, 6.0, 3.0)
        
    def generate_vase():
        vase_steps = []
        base_layers = 5
        total_layers = int(total_height / layer_height)
        
        # Smooth flat floor
        for l_idx in range(base_layers):
            lz = l_idx * layer_height
            for r_idx in range(int(base_radius/0.52) + 1, 5, -1):
                r = r_idx * 0.52
                for seg in range(73):
                    angle = (seg / 72) * 2.0 * math.pi
                    vase_steps.append(fc.Point(x=center_x + r*math.cos(angle), y=center_y + r*math.sin(angle), z=lz))
                    
        # Twisted Ribbon Shell
        for l_idx in range(base_layers, total_layers):
            lz_base = l_idx * layer_height
            helix_shift = lz_base * twist_rate
            factor = min(1.0, (lz_base - 5.0) / 15.0) if lz_base > 5.0 else 0.0
            
            for seg in range(145):
                angle = (seg / 144) * 2.0 * math.pi
                # Add geometric ripple variance
                ripple = math.sin(angle * 12.0 + helix_shift) * ripple_depth * factor
                r = base_radius + ripple
                x = center_x + r * math.cos(angle + helix_shift)
                y = center_y + r * math.sin(angle + helix_shift)
                vase_steps.append(fc.Point(x=x, y=y, z=lz_base))
        return vase_steps
        
    steps = generate_vase()
    filename = "organic_twisted_vase.gcode"

# =====================================================================
# MODEL 3: PARAMETRIC SQUISHY FIDGET TILE
# =====================================================================
else:
    st.subheader("⚙️ Fidget Customization Parameters")
    col1, col2 = st.columns(2)
    with col1:
        tile_size = st.slider("Tile Width/Length (mm)", 20.0, 80.0, 40.0)
        wave_pattern = st.slider("Wave Density (Frequency)", 0.1, 1.0, 0.4, step=0.1)
    with col2:
        spring_amplitude = st.slider("Fidget Spring Squash (mm)", 1.0, 4.0, 2.0)
        
    def generate_fidget():
        fid_steps = []
        cell_size = 8.0
        total_layers = int(12.0 / layer_height) # Standard 12mm thick toy pocket pocket
        min_x, min_y = center_x - (tile_size/2.0), center_y - (tile_size/2.0)
        
        # Generates a flexible wave spring tile configuration
        for l_idx in range(total_layers):
            lz = l_idx * layer_height
            factor = math.sin((lz / 12.0) * math.pi) # Bulges physical spring compliance mid-body
            
            for gy in range(int(tile_size / cell_size)):
                y_start = min_y + (gy * cell_size)
                for gx in range(int(tile_size / cell_size)):
                    x_start = min_x + (gx * cell_size)
                    
                    for step_idx in range(11):
                        t = step_idx / 10
                        x = x_start + (t * cell_size)
                        # Adds a horizontal and vertical gyroscopic wobble shift
                        y_bend = spring_amplitude * math.sin(x * wave_pattern + lz) * factor
                        y = y_start + (t * cell_size) + y_bend
                        z = lz + (spring_amplitude * math.cos(x * wave_pattern) * factor)
                        fid_steps.append(fc.Point(x=x, y=y, z=z))
        return fid_steps
        
    steps = generate_fidget()
    filename = "squishy_fidget_tile.gcode"

# =====================================================================
# --- 4. G-CODE COMPILATION ENGINE & EXPORT ---
# =====================================================================
if steps:
    st.success(f"Mathematical mesh model computed successfully! (Vectors: {len(steps)})")
    
    # Process code parameter dictionary conversions
    print_settings = {
        'extrusion_width': nozzle_diameter + 0.04,
        'extrusion_height': layer_height,
        'print_speed': print_speed * 60, # Converts mm/s to standard machine mm/min
        'nozzle_temp': nozzle_temp,
        'bed_temp': bed_temp
    }
    
    # Compile text strings safely through the conversion matrix
    gcode_output = fc.transform(
        steps, 
        'gcode', 
        fc.GcodeControls(
            printer_name='bambulab_x1', 
            initialization_data=print_settings
        )
    )
    
    # Clean first layer override mapping injection
    gcode_output = gcode_output.replace(f"G1 F{print_speed * 60}", "G1 F900", 1)
    
    # Direct Web Application System Download Prompt
    st.download_button(
        label="💾 Download Ready-to-Print G-Code",
        data=gcode_output,
        file_name=filename,
        mime="text/plain"
    )
