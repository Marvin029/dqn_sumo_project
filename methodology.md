# Methodology

## 3.1 Study Design Overview

This study compares two controllers at a single urban intersection under identical conditions: a fixed-time baseline and a learning-based Deep Q-Network (DQN) controller. The goal is to evaluate whether a learning controller can allocate green time more responsively than a preset plan while keeping the setup transparent and reproducible. The scope is intentionally intersection-level so that assumptions, inputs, and outcomes can be specified clearly, repeated, and extended later.

## 3.2 Project Preparation

This section describes what is prepared before any data work: hardware/resources to run the simulations and training, and the software toolchain that defines how the environment is built, controlled, and evaluated.

### 3.2.1 Hardware Requirements

We assume a workstation capable of running microscopic simulation and training a compact value-based agent. At a general level, this includes: a multi-core CPU for simulation and logging, sufficient RAM for repeated runs, and a CUDA-capable GPU if training acceleration is desired; storage should accommodate run logs, summaries, and checkpoints. The study is designed to remain feasible on a modest research setup by using a single-intersection network and compact models.

(We still have to add a short line on the actual machine used in development and the minimum viable configuration for replication; exact specs go to the Appendix.)

### 3.2.2 Software Requirements

The workflow uses open and commonly used tools: SUMO as the microscopic traffic simulator; TraCI to interface with controllers; and a standard deep learning framework for DQN. For environment build and editing, we rely on OpenStreetMap (OSM) data with netconvert to generate the network and NetEdit for adjustments and validation. Scenario and run orchestration use basic scripting (e.g., Python), while metric computation and artifact packaging use standard data-processing libraries.

(We still have to list tool versions and key packages; include version pins and installation notes in the Appendix. Screenshots or CLI examples for OSM→netconvert and NetEdit checks should also be placed there.)

## 3.3 Data Processing

Data processing prepares three elements in sequence: (1) site-derived inputs that configure the fixed-time baseline and ground the environment in local practice; (2) a shared simulation setup used by both controllers; and (3) simulator-generated scenarios that serve as training and evaluation data. Across scenarios, the environment is fixed while realized traffic conditions vary in a controlled and repeatable way.

### 3.3.1 Data Collection

We document on-site operational notes needed to configure the fixed-time plan and to align the simulation with observed practice. These notes cover the cycle structure, phase order, approximate green splits, intergreen and clearance logic, and any site-specific constraints relevant to safe movements. They function as configuration inputs, not as training data for the learning controller.

(We still have to compile a concise paragraph of the actual items gathered during the site check—e.g., observed phase sequence, typical cycle-length range, any notable local rules—keeping numeric details for the Appendix.)

### 3.3.2 Data Preprocessing

Collected notes are translated into a clear baseline specification and a single SUMO environment that both controllers will use. The environment includes the intersection network and permitted movements (derived from OSM with netconvert and refined with NetEdit), route templates consistent with the site, and virtual detectors near stop lines that provide presence, queue/occupancy, and short-segment travel-time signals. In addition, we define in general terms how scenarios will vary and how randomness is controlled so that generation remains reproducible across runs and across controllers.

(We still have to provide a brief validation note confirming that the coded geometry and permitted turns match the site, and that detector locations provide feasible state signals. Keep coordinates, file paths, and any screenshots in the Appendix.)

### 3.3.3 Scenario Generation (Training and Evaluation Data)

Using the shared environment and the high-level scenario design, we generate scenarios within the simulator under controlled seeds. The constants across scenarios are the network topology, phase template, detector placements, and target vehicle-class shares; the variables are realized arrivals by approach and the route choices vehicles take through the junction. These generated scenarios supply the learning experiences for DQN training and the matched conditions for evaluating both controllers.

Scenarios cover low/medium/high demand bands (e.g., 50-150 vehicles/hour total) and typical vs. peak composition (e.g., varying priority vehicle shares from 0.5% to 2%). Route generation uses SUMO's randomTrips.py with fixed seeds for reproducibility (e.g., seeds 1-5 for independent runs).

## 3.4 Model Development

We define the two controllers and summarize the training approach for the learning-based controller, keeping the discussion conceptual and leaving numeric settings and code-level details to the Appendix.

### 3.4.1 Purpose and Scope

Two controllers are developed for comparison under identical inputs and protocol: a non-learning fixed-time reference and a learning-based DQN controller. This section specifies the roles of each controller and the information they consume, so that differences in outcomes are attributable to control logic rather than setup. The objective is not to exhaustively optimize either controller, but to establish a clear, reproducible benchmark at the intersection scale. Where implementation details are necessary for replication, they are provided in the Appendix to preserve readability in the main text.

### 3.4.2 Baseline Controller: Fixed-Time

The fixed-time baseline follows a preset cycle with a fixed phase order, predetermined green splits, and defined clearance intervals. Its parameters are frozen before testing and applied unchanged across all scenarios to provide a stable point of comparison. The baseline consumes only the schedule and signal state; it does not adapt to detector readings or modify its plan during runs. This design aligns the baseline with common practice while enabling a straightforward, interpretable reference against which the learning controller is evaluated.

(We still have to include a short verbal snapshot of the baseline’s phase sequence and any protected turns, with the exact cycle time, split values, and clearance durations placed in the Appendix.)

### 3.4.3 Learning-Based Controller: DQN (High-Level Formulation)

#### 3.4.3.1 Problem Framing

Intersection control is treated as sequential decision making: at each step the agent observes the intersection state, selects an action, receives a reward, and updates its policy over many episodes. The agent interacts with the same simulated environment as the baseline, ensuring comparability. By defining a compact state and discrete action set that reflect real signal capabilities, the formulation keeps learning tractable while maintaining operational relevance.

#### 3.4.3.2 Observation (State) Design

The state aggregates detector-derived measures near the stop lines (queues or occupancy and short-segment travel time) and minimal signal context (current phase and elapsed green). These features are readily obtained in the simulator and align with what practical detectors can supply, supporting eventual translation beyond simulation. The state is intentionally compact to reduce model complexity, improve learning stability, and keep the evaluation reproducible across seeds.

(We still have to confirm the final list of state elements and any normalizations; exact encodings belong in the Appendix.)

#### 3.4.3.3 Action Space

Actions correspond to realistic controller operations for an isolated junction: hold the current phase for a short extension or switch to the next permitted phase under safety constraints. Mapping actions this way preserves the correspondence between decisions made by the learning agent and feasible actions in field controllers. It also simplifies benchmarking by keeping the action set consistent across scenarios and evaluation runs.

#### 3.4.3.4 Reward Design

The reward signals progress toward timing efficiency by penalizing delay and queues, while applying a modest penalty to discourage unnecessary switching. Optional priority-sensitive terms may be included conceptually if site conditions require, but the core structure remains delay- and queue-oriented to stay aligned with reported indicators. Coefficients and normalizations are documented in the Appendix so that others can reproduce the incentive structure exactly.

(We still have to finalize the exact reward expression and coefficients; these go to the Appendix, with the main text staying at the concept level.)

### 3.4.4 Training Summary

Training is conducted in the same SUMO environment used for evaluation so that learned behavior reflects the final test conditions. Episodes present generated scenarios under controlled seeds; the agent learns using experience replay and a fixed target network update schedule to improve stability. Early stopping or checkpoint selection is based on a simple stability or validation rule to avoid overfitting to idiosyncratic scenarios. All hyperparameters, schedules, and implementation details, including the controller–simulator interface, are recorded in the Appendix to enable precise replication.

(We still have to state the checkpoint selection rule in one line, e.g., “best mean delay on a held-out scenario set” or “latest stable window without degradation.” All hyperparameters, update intervals, and schedules go to the Appendix.)

Implementation note. Details of the controller–simulator interface (e.g., TraCI-based state retrieval, action execution, reward logging, and episode control) are provided in the Appendix to keep this chapter focused on roles and procedures.

## 3.5 Evaluation

A shared protocol is used to execute both controllers on identical scenarios, and outcomes are reported through a small set of timing-efficiency indicators. Result summaries and run artifacts are organized to support independent checks and reproduction.

### 3.5.1 Common Execution Protocol

Both controllers run on the same network geometry, permitted movements, detector layout, and scenario set to isolate the effect of control logic. Each run starts with a warm-up period followed by a defined scoring window; this avoids initialization bias and ensures metrics are computed under steady operating conditions. Multiple seeds are used for reliability, with identical seeds applied to both controllers so that random variation in arrivals and routes is matched. Controller decisions, per-run summaries, and key environment versions are logged to support auditability and re-runs.

(We still have to confirm the warm-up and scoring durations and the number of seeds; exact values belong in the Appendix. A short note on file naming and run metadata should also be added there.)

### 3.5.2 Metrics and Improvement Criterion

Timing efficiency is evaluated using four indicators computed identically for all controllers: average delay per vehicle (primary), average queue length, local travel time across the junction, and throughput. Delay is emphasized because it reflects user experience directly at the junction, while the other indicators guard against improvements that merely shift congestion elsewhere. An outcome is considered an improvement when delay decreases without meaningful deterioration in queue length, travel time, or throughput. This multi-metric rule mirrors common reporting practice and supports like-for-like interpretation across studies.

(If we plan to track supplementary measures such as average stops or priority-vehicle delay, mention them briefly in the Appendix and keep the four core indicators central here.)

### 3.5.3 Reporting and Aggregation

Results are summarized per scenario and then aggregated across scenarios and seeds to obtain stable estimates of performance. For transparency, we provide a compact results package that includes run logs, per-run metric summaries, configuration snapshots, and minimal documentation of the execution protocol. This bundle enables others to replicate runs, verify calculations, and extend the benchmark to alternative controllers or additional scenarios. The structure of filenames and the schema of result CSVs are kept consistent so that comparisons can be automated with simple scripts.

(We still have to specify the artifact bundle format—e.g., CSV summaries, log files, and a minimal README—kept in the Appendix.)

## Appendices

### A.1 Hardware and Software Details (for §3.2.1–3.2.2)

Specific figures from subsections 3.2.1–3.2.2 go here labeled {A.1 System Specs and Tool Versions}: Development machine: Windows 10, Intel Core i5 multi-core CPU, 16GB RAM, no dedicated CUDA-capable GPU, 500GB SSD storage. Minimum viable configuration for replication: multi-core CPU (e.g., Intel i3 or equivalent), 8GB RAM, 100GB storage. SUMO version 1.18.0, TraCI interface version 1.18.0, deep learning framework PyTorch 2.0.1, key libraries Gymnasium 0.29.1, Stable-Baselines3 2.0.0, NumPy 1.24.3, Pandas 2.0.3, Matplotlib 3.7.2. OSM → netconvert options: Default for single intersection. NetEdit screenshots or validation notes: Geometry matches 4-way intersection with 1 lane per approach. Installation steps: Install SUMO 1.18.0 and add tools to PYTHONPATH; pip install gymnasium stable-baselines3 torch numpy pandas matplotlib.

### A.2 Baseline Parameters (for §3.4.2)

Specific figures from subsection 3.4.2 go here labeled {A.2 Baseline Cycle and Splits}: Cycle length 60s, phase order NS green (30s) → yellow (3s) → all-red (1s) → EW green (30s) → yellow (3s) → all-red (1s), protected/permitted turn details none specified.

### A.3 Environment and Detectors (for §3.3.2)

Specific figures from subsection 3.3.2 go here labeled {A.3 Network and Detector Layout}: Network file references net.net.xml, permitted movement table standard 4-way, detector coordinates and types virtual near stop lines (4 lanes), geometry–turn validation notes: Matches simple intersection layout.

### A.4 Scenario Design and Seeds (for §3.3.3)

Specific figures from subsection 3.3.3 go here labeled {A.4 Scenario Ranges and Seed Policy}: Demand bands low/medium/high (e.g., 50-150 vehicles/hour), vehicle-class share tables ~65% passenger, 15% motorcycle, 10% bus, 10% moped, 1% emergency, route-generation notes via randomTrips.py, seed assignment policy fixed for reproducibility (e.g., seeds 1-5), list of scenario IDs generated under controlled seeds.

### A.5 State, Action, Reward Details (for §3.4.3)

Specific figures from subsections 3.4.3.2–3.4.3.4 go here labeled {A.5 State Encoding and Reward Coefficients}: Exact state encodings: 11 dimensions - 4 queue lengths (halting vehicles per approach, 0-1000), 1 total waiting time (sum across all vehicles, 0-60), 1 phase (0 for NS green, 1 for EW green), 1 total priority count (emergency vehicles, 0-10000), 4 per-approach priority counts (0-1000). Reward formula: Reward_t = – (α × normalized_avg_delay_t + β × normalized_avg_queue_t) – κ × I[switch_t] – φ × normalized_priority_delay_t, coefficients α=1.0, β=0.5, κ=0.1, φ=2.0, normalizations normalized_avg_delay = avg_delay / 60, normalized_avg_queue = avg_queue / 20, normalized_priority_delay = priority_delay / 60.

### A.6 Training Settings (for §3.4.4)

Specific figures from subsection 3.4.4 go here labeled {A.6 DQN Hyperparameters and Schedule}: Model architecture 2 hidden layers × 64 neurons each, ReLU activations, optimizer Adam, learning rate 0.0005, discount factor γ=0.95, replay buffer size 50,000, minibatch size 64, target update interval 500 steps, epsilon decay 1.0 → 0.05 over 10,000 steps, episode length 3,600 steps, checkpoint selection rule latest stable window without degradation (e.g., best mean delay on a held-out scenario set).

### A.7 Execution Protocol Details (for §3.5.1)

Specific figures from subsection 3.5.1 go here labeled {A.7 Protocol Windows and Run Counts}: Warm-up duration 600s, scoring window 3,000s, number of seeds 5, runs per scenario 1, run-script outline: Use train_dqn.py for training, evaluate_model.py for evaluation.

### A.8 Metrics and Computation (for §3.5.2)

Specific figures from subsection 3.5.2 go here labeled {A.8 Metric Definitions and Formulas}: Precise metric definitions: Average delay = total wait / num vehicles, average queue length = total halting / 4, throughput = departed vehicles / hour, local travel time = avg time from entry to exit. Supplementary indicators: Priority delay (separate for emergency vehicles).

### A.9 Artifacts and Reproducibility (for §3.5.3)

Specific figures from subsection 3.5.3 go here labeled {A.9 Logs, Summaries, and Metadata}: File list and formats: models/ (checkpoints in .zip), logs (per-run text files), summaries CSV. Schema for per-run CSVs: Columns for delay, queue, throughput, travel time, priority delay. Log naming conventions: dqn_sumo_seed{seed}_{timesteps}_steps.zip. Minimal README: Steps to run simple.sumocfg with SUMO, load model in run_dqn_control.py.


Core Dependencies (from requirements.txt):
gymnasium: For the reinforcement learning environment interface.
stable-baselines3: For implementing the DQN algorithm.
torch: PyTorch for neural network computations (used by Stable-Baselines3).
traci: SUMO's Traffic Control Interface for Python integration.
sumolib: SUMO's library for network and route handling.
numpy: For numerical computations and data handling.
pandas: For data analysis and metric computation.
matplotlib: For plotting and visualization of results.