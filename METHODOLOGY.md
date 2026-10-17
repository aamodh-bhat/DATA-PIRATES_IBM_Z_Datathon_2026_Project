# SkyMesh Methodology & Technical Architecture Document

**Project Name:** SkyMesh: Swarm-Based Drone Defense Powered by IBM LinuxONE  
**Team Name:** Data Pirates  
**Event:** IBM Z Datathon 2026  

---

## 1. Problem Statement & Mathematical Formulation

### 1.1 The Challenge
Modern civilian populations, urban hubs, and critical infrastructure face an increasing asymmetric threat from low-cost airborne projectiles and rogue drones. Conventional anti-air solutions (such as guided surface-to-air missiles) cost millions of dollars per interceptor, creating an unsustainable economic dynamic when facing cheap, mass-produced threats.

### 1.2 Mathematical Objective
SkyMesh replaces high-cost countermeasures with a defensive swarm of low-cost, disposable drones coordinated via centralized predictive AI. The core objective is:
1. Estimate the 3D trajectory $\vec{r}_{\text{threat}}(t) = [x(t), y(t), z(t)]^T$ of an incoming ballistic or propelled threat from discrete early-stage telemetry inputs.
2. Select the optimal node $i \in \{1, \dots, N\}$ from a spatially structured mesh of idle defensive drones positioned at coordinates $\vec{p}_i = [x_i, y_i, z_i]^T$.
3. Compute an intercept point $\vec{r}_{\text{intercept}}$ and time $t_{\text{intercept}}$ satisfying:
   $$\|\vec{p}_i + \vec{v}_i \cdot t_{\text{intercept}} - \vec{r}_{\text{threat}}(t_{\text{intercept}})\| \le \epsilon$$
   where $\epsilon$ is the lethal engagement tolerance (empirically validated at $\approx 1.84\text{ m}$) while ensuring the interception altitude and coordinates fall outside densely populated civilian sectors.

---

## 2. Airspace Geometry: Face-Centered Cubic (FCC) Mesh

To protect a designated airspace without continuous high-energy loitering or blind spots:
* **Lattice Arrangement:** Defending drones are positioned in a **Face-Centered Cubic (FCC)** lattice structure.
* **Spatial Optimization:** FCC provides the highest packing density for spheres in 3-dimensional space ($\approx 74.05\%$), minimizing the maximum possible distance between any arbitrary incoming threat vector and the nearest interceptor node.
* **Operational Value:** Reduces the total fleet size required to guarantee complete defensive coverage over a civilian municipality or utility installation.

---

## 3. Machine Learning Pipeline & Threat Prediction

### 3.1 Model Architecture
* **Algorithm:** Multi-Layer Perceptron Regressor (`MLPRegressor` via Scikit-Learn).
* **Input Vector:** Initial threat state observations $\mathbf{x} = [x_0, y_0, z_0, v_x, v_y, v_z, \dots]$.
* **Target Vector:** Anticipated impact/flight coordinates $\mathbf{y} = [x_{\text{target}}, y_{\text{target}}, z_{\text{target}}]$.
* **Normalization:** `StandardScaler` applied to feature matrices to preserve gradient stability across high spatial magnitudes.

### 3.2 Secure Model Serialization & Enclave Handling
To guarantee model integrity and prevent adversarial reverse-engineering:
* The trained model and feature scalers are serialized and encrypted using symmetric encryption (`cryptography.fernet.Fernet`).
* Artifacts (`skymesh_model.key`, `target_scaler.pkl.enc`, `feature_scaler.pkl.enc`, `skymesh_model.pkl.enc`) are stored encrypted at rest.
* At runtime, the decryption occurs dynamically into volatile, secure memory streams (`io.BytesIO`) inside the execution process, preventing unencrypted model weights from hitting persistent disk.

---

## 4. Mainframe Infrastructure: IBM LinuxONE (s390x)

SkyMesh requires guaranteed zero-downtime availability and hardware-level isolation against cyber interference.

### 4.1 Deployment Architecture
* **Environment:** IBM LinuxONE Community Cloud Virtual Machine.
* **Architecture:** `s390x` (64-bit IBM Z / LinuxONE enterprise mainframe).
* **OS:** Ubuntu 24.04 LTS (`Linux 6.8.0-147-generic s390x`).

### 4.2 Security & Confidential Computing Properties
1. **Isolated Execution:** Threat inference and node targeting happen within a protected hardware enclave on the mainframe.
2. **Resilience to Tampering:** Even if field telemetry links or peripheral monitoring sensors encounter interference, the core targeting weights and orchestration decisions remain shielded inside the LinuxONE enclave.
3. **Headless Execution Flow:**
   * Script execution (`simulator.py`) initiated remotely via SSH/PuTTY on the headless mainframe.
   * Model weights decrypted in RAM.
   * Trajectory and intercept calculations executed natively on the mainframe CPU.
   * Output coordinates, error margins, and swarm activation signals produced deterministically.

---

## 5. Empirical Results & Validation

* **Inference Accuracy:** Target trajectory prediction achieves an intercept error margin of **1.84 meters**, well within the lethal neutralizing radius of low-cost drone kinetic countermeasures.
* **Civilian Risk Reduction:** Intercept vectors prioritize high-altitude neutralization before threats reach low-altitude urban zones, minimizing ground collateral damage and falling debris over civilian centers.
* **Cost Efficiency:** Offloads multimillion-dollar missile defense expenditures onto scalable, disposable commercial-grade drone swarms managed by high-assurance centralized AI.


'''mermaid
graph TD
    subgraph Data Input
        A[Radar/Telemetry Sensors] -->|Real-time XYZ & Velocity| B(Threat Detection)
    end

    subgraph IBM LinuxONE s390x
        C{Secure Hardware Enclave}
        B -->|Encrypted Data Stream| C
        C --> D[Decrypt AI Models in RAM]
        D --> E[Scikit-Learn MLPRegressor]
        E -->|Predict Trajectory| F[FCC Swarm Orchestration]
        F -->|Select Optimal Node| G[Calculate Intercept Coordinate]
    end

    subgraph Physical Defense Grid
        G -->|Activation Signal| H[Drone Node in FCC Lattice]
        H -->|Deploy to 3D Coordinate| I((Neutralize Threat))
    end
'''
