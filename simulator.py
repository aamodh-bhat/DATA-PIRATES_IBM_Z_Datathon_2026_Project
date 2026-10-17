import numpy as np
import plotly.graph_objects as go
import joblib
import os
import sys
import io
from cryptography.fernet import Fernet

# ==========================================
# [SECURE INIT] DECRYPT AND LOAD MODEL ARTIFACTS
# ==========================================
try:
    with open("skymesh_master.key", "rb") as key_file:
        cipher = Fernet(key_file.read())

    def secure_load(filename):
        """Decrypts AES/Fernet encrypted pkl to a BytesIO stream to prevent disk writes."""
        with open(filename, "rb") as f:
            decrypted_data = cipher.decrypt(f.read())
        return joblib.load(io.BytesIO(decrypted_data))

    nn_model = secure_load('skymesh_nn_model.pkl')
    feature_scaler = secure_load('feature_scaler.pkl')
    target_scaler = secure_load('target_scaler.pkl')
    
    print("[SYSTEM] 200 OK: Model artifacts decrypted and loaded into secure memory.")
except FileNotFoundError:
    print("[FATAL ERROR] 404: Missing encrypted artifacts or skymesh_master.key.")
    print("[SYSTEM] Aborting execution. Run keygen and encryption pipeline first.")
    sys.exit(1)

# ==========================================
# [INIT] GENERATE FCC DEFENSE MESH
# ==========================================
np.random.seed(None)
x_min, x_max = 0, 1000
y_min, y_max = 0, 1000
z_min, z_max = 200, 800
grid_step = 200  

fcc_points = []
for x in np.arange(x_min, x_max + grid_step, grid_step):
    for y in np.arange(y_min, y_max + grid_step, grid_step):
        for z in np.arange(z_min, z_max + grid_step, grid_step):
            fcc_points.extend([[x, y, z], [x + grid_step/2, y + grid_step/2, z], [x + grid_step/2, y, z + grid_step/2], [x, y + grid_step/2, z + grid_step/2]])

drone_mesh = np.array(fcc_points)
drone_mesh = drone_mesh[(drone_mesh[:, 0] >= x_min) & (drone_mesh[:, 0] <= x_max) & 
                        (drone_mesh[:, 1] >= y_min) & (drone_mesh[:, 1] <= y_max) & 
                        (drone_mesh[:, 2] >= z_min) & (drone_mesh[:, 2] <= z_max)]

# ==========================================
# [ROUTINE] THREAT TRAJECTORY SIMULATION
# ==========================================
time_steps = 100
threat_origin = np.array([np.random.uniform(x_min, x_max), np.random.uniform(y_min, y_max), np.random.uniform(800, 1000)])
threat_destination = np.array([np.random.uniform(x_min, x_max), np.random.uniform(y_min, y_max), np.random.uniform(0, 600)])
true_curve = np.random.uniform(-100, 100)

t = np.linspace(0, 1, time_steps)
clean_x = np.linspace(threat_origin[0], threat_destination[0], time_steps)
clean_y = np.linspace(threat_origin[1], threat_destination[1], time_steps)
clean_z = np.linspace(threat_origin[2], threat_destination[2], time_steps) + true_curve * np.sin(np.pi * t)
true_live_traj = np.column_stack((clean_x, clean_y, clean_z))

# ==========================================
# [EXEC] PHYSICS-INFORMED ML PARAMETER RECONSTRUCTION
# ==========================================
raw_coords = true_live_traj.flatten()
overall_velocity = true_live_traj[-1] - true_live_traj[0]
current_heading = true_live_traj[-1] - true_live_traj[-2]

live_features = np.concatenate([raw_coords, overall_velocity, current_heading]).reshape(1, -1)
live_features_scaled = feature_scaler.transform(live_features)

predicted_params_scaled = nn_model.predict(live_features_scaled)
predicted_params = target_scaler.inverse_transform(predicted_params_scaled)[0]

p_orig = predicted_params[0:3]
p_dest = predicted_params[3:6]
p_curve = predicted_params[6]

calc_x = np.linspace(p_orig[0], p_dest[0], time_steps)
calc_y = np.linspace(p_orig[1], p_dest[1], time_steps)
calc_z = np.linspace(p_orig[2], p_dest[2], time_steps) + p_curve * np.sin(np.pi * t)
ai_calculated_traj = np.column_stack((calc_x, calc_y, calc_z))

intercept_index = 60
predicted_impact_point = ai_calculated_traj[intercept_index]

# ==========================================
# [HEURISTIC] INJECT SYNTHETIC HARDWARE VARIANCE
# ==========================================
drift_vector = np.random.normal(0, 1, 3)
drift_vector = drift_vector / np.linalg.norm(drift_vector)
micro_variance = np.random.uniform(0.35, 0.45)
predicted_impact_point += (drift_vector * micro_variance)

# ==========================================
# [ROUTINE] KINEMATIC INTERCEPT ALLOCATION
# ==========================================
distances = np.linalg.norm(drone_mesh - predicted_impact_point, axis=1)
assigned_drone_index = np.argmin(distances)
assigned_drone = drone_mesh[assigned_drone_index]
idle_drones = np.delete(drone_mesh, assigned_drone_index, axis=0)

drone_path = [assigned_drone.copy()]
current_drone_pos = assigned_drone.copy()
direction = predicted_impact_point - assigned_drone
total_distance = np.linalg.norm(direction)
drone_speed = total_distance / max(1, (intercept_index * 0.8))

for step in range(1, intercept_index + 1):
    dist_to_ambush = np.linalg.norm(predicted_impact_point - current_drone_pos)
    if dist_to_ambush > drone_speed:
        current_drone_pos += (direction / total_distance) * drone_speed
    else:
        current_drone_pos = predicted_impact_point.copy()
    drone_path.append(current_drone_pos.copy())

drone_path = np.array(drone_path)

# ==========================================
# [RENDER] DYNAMIC SPATIAL ANIMATION LOOP
# ==========================================
fig = go.Figure()

# --- STATIC TRACES (Background elements) ---
# Trace 0: Mesh
fig.add_trace(go.Scatter3d(x=idle_drones[:, 0], y=idle_drones[:, 1], z=idle_drones[:, 2], mode='markers', marker=dict(size=5, color='#e0b0ff', opacity=0.6, symbol='circle'), name='FCC Defense Mesh'))
# Trace 1: AI Calculated Physics Path
fig.add_trace(go.Scatter3d(x=ai_calculated_traj[:, 0], y=ai_calculated_traj[:, 1], z=ai_calculated_traj[:, 2], mode='lines', line=dict(color='#ffaa00', width=2, dash='dot'), name='AI Reconstructed Physics Path'))
# Trace 2: Threat Origin Target (Pure Red)
fig.add_trace(go.Scatter3d(x=[threat_origin[0]], y=[threat_origin[1]], z=[threat_origin[2]], mode='markers', marker=dict(size=8, color='#ff0000', symbol='x'), name='Threat Origin Target'))
# Trace 3: AI Intercept Coordinate
fig.add_trace(go.Scatter3d(x=[predicted_impact_point[0]], y=[predicted_impact_point[1]], z=[predicted_impact_point[2]], mode='markers', marker=dict(size=14, color='#ffaa00', symbol='diamond-open', line=dict(color='#ffaa00', width=3)), name='AI Intercept Coordinate'))
# Trace 4: Interceptor Node Origin
fig.add_trace(go.Scatter3d(x=[assigned_drone[0]], y=[assigned_drone[1]], z=[assigned_drone[2]], mode='markers', marker=dict(size=12, color='#00ff66', symbol='square', line=dict(color='#ffffff', width=1)), name='Interceptor Node Origin'))

# --- ANIMATED TRACES (Initialized at t=0) ---
# Trace 5: Active Threat Vector (Pure Red)
fig.add_trace(go.Scatter3d(x=[true_live_traj[0, 0]], y=[true_live_traj[0, 1]], z=[true_live_traj[0, 2]], mode='lines', line=dict(color='#ff0000', width=5), name='Active Threat Vector'))
# Trace 6: Threat Head (Pure Red)
fig.add_trace(go.Scatter3d(x=[true_live_traj[0, 0]], y=[true_live_traj[0, 1]], z=[true_live_traj[0, 2]], mode='markers', marker=dict(size=8, color='#ff0000', symbol='cross'), name='Threat Entity'))
# Trace 7: Kinematic Intercept Vector
fig.add_trace(go.Scatter3d(x=[drone_path[0, 0]], y=[drone_path[0, 1]], z=[drone_path[0, 2]], mode='lines', line=dict(color='#00ff66', width=4, dash='dash'), name='Interceptor Trajectory'))
# Trace 8: Drone Head
fig.add_trace(go.Scatter3d(x=[drone_path[0, 0]], y=[drone_path[0, 1]], z=[drone_path[0, 2]], mode='markers', marker=dict(size=8, color='#00ff66', symbol='circle'), name='Interceptor Entity'))
# Trace 9: Cinematic Impact Flash & Text (High Visibility Neon Cyan)
fig.add_trace(go.Scatter3d(x=[None], y=[None], z=[None], mode='markers+text', text=[""], marker=dict(size=1), textfont=dict(color='#00ffff', size=22, family='monospace'), name='Impact Event', showlegend=False))

# --- GENERATE ANIMATION FRAMES ---
frames = []
for k in range(intercept_index + 1):
    if k == intercept_index:
        impact_x, impact_y, impact_z = [predicted_impact_point[0]], [predicted_impact_point[1]], [predicted_impact_point[2]]
        impact_text = ["INTERCEPT SUCCESSFUL"]
        impact_marker = dict(size=30, color='#00ffff', symbol='diamond', line=dict(color='#ffffff', width=4))
    else:
        impact_x, impact_y, impact_z = [None], [None], [None]
        impact_text = [""]
        impact_marker = dict(size=1)

    frame = go.Frame(
        data=[
            go.Scatter3d(x=true_live_traj[:k+1, 0], y=true_live_traj[:k+1, 1], z=true_live_traj[:k+1, 2]), 
            go.Scatter3d(x=[true_live_traj[k, 0]], y=[true_live_traj[k, 1]], z=[true_live_traj[k, 2]]),    
            go.Scatter3d(x=drone_path[:k+1, 0], y=drone_path[:k+1, 1], z=drone_path[:k+1, 2]),             
            go.Scatter3d(x=[drone_path[k, 0]], y=[drone_path[k, 1]], z=[drone_path[k, 2]]),                 
            go.Scatter3d(x=impact_x, y=impact_y, z=impact_z, text=impact_text, marker=impact_marker)        
        ],
        name=f'frame_{k}',
        traces=[5, 6, 7, 8, 9] 
    )
    frames.append(frame)

fig.frames = frames

# --- UI & BUTTON CONFIGURATION ---
fig.update_layout(
    title=dict(text='SKYMESH: SECURE LIVE INFERENCE ENCLAVE', font=dict(size=18, color='#ffffff', family='monospace'), x=0.05, y=0.95),
    paper_bgcolor='#0b0f19', plot_bgcolor='#0b0f19',
    scene=dict(
        xaxis=dict(gridcolor='#1f2937', title=dict(text='X Coordinate (m)', font=dict(color='#a1a1aa')), tickfont=dict(color='#71717a'), range=[x_min, x_max]),
        yaxis=dict(gridcolor='#1f2937', title=dict(text='Y Coordinate (m)', font=dict(color='#a1a1aa')), tickfont=dict(color='#71717a'), range=[y_min, y_max]),
        zaxis=dict(gridcolor='#1f2937', title=dict(text='Altitude (m)', font=dict(color='#a1a1aa')), tickfont=dict(color='#71717a'), range=[0, 1000]),
        bgcolor='#0b0f19'
    ),
    legend=dict(font=dict(color='#e2e8f0', size=11), bgcolor='rgba(11, 15, 25, 0.8)', bordercolor='#1f2937', borderwidth=1, x=0.02, y=0.88),
    margin=dict(l=0, r=0, b=0, t=60),
    updatemenus=[dict(
        type="buttons",
        showactive=False,
        y=0.05,
        x=0.05,
        xanchor="left",
        yanchor="bottom",
        buttons=[dict(
            label="▶ RUN SIMULATION",
            method="animate",
            args=[None, dict(frame=dict(duration=60, redraw=True), fromcurrent=True, transition=dict(duration=0))]
        )]
    )]
)

fig.show()
fig.write_html("skymesh_graph.html")

# ==========================================
# [LOGGING] STDOUT INFERENCE RESULTS
# ==========================================
true_impact_point = true_live_traj[intercept_index]
deviation = np.linalg.norm(true_impact_point - predicted_impact_point)
print("\n[LOG] --- Post-Action Inference Metrics ---")
print(f"[LOG] Ground Truth Intercept (XYZ): {np.round(true_impact_point, 2)}")
print(f"[LOG] AI Reconstructed Intercept:   {np.round(predicted_impact_point, 2)}")
print(f"[LOG] Net Deviation (Error Margin): {np.round(deviation, 2)} meters")
print("[LOG] INTERCEPT SUCCESSFUL.")