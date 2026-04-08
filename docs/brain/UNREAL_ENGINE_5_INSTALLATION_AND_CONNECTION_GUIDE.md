# 📘 UNREAL ENGINE 5: INSTALLATION AND CONNECTION GUIDE

This guide provides the complete, step-by-step path to taking your historical simulation from a Python backend to a high-fidelity Unreal Engine 5 tactical 3D environment.

---

## 🏗️ STEP 1: Setting Up Your Environment

To handle large-scale C++ simulations, you need the professional development stack.

### 1. The Engine: Unreal Engine 5.3+
- Download and install the **Epic Games Launcher**.
- Go to the **Unreal Engine** tab > **Library**.
- Click **(+)** to add a new engine version and select **5.3** or **5.4**.
- Click **Install**.

### 2. The Hammer: Visual Studio 2022
Unreal Engine requires Visual Studio to compile C++ code.
- Download **Visual Studio 2022 Community** (Free).
- **CRITICAL**: During installation (in the "Workloads" tab), you **MUST** select:
    - `[x]` **Game development with C++**
    - Under the "Installation Details" on the right, ensure `[x]` **Unreal Engine installer** is checked.
- Restart your computer after installation.

---

## 📁 STEP 2: Creating Your Unreal Project

1. Launch Unreal Engine 5.
2. Select **Games > Blank**.
3. **CRITICAL SETTINGS**:
    - Project Type: **C++** (Not Blueprint)
    - Starter Content: **Checked**
    - Name: `BattleSim`
4. Click **Create**. Visual Studio will open automatically—you can minimize it for now.

---

## 🔗 STEP 3: Connecting the WarSim Bridge

I have prepared the bridge files for you. Copy them into your new project.

1. Locate the `WarSimWebSocketClient` files in:
   `c:\Users\t3sfo\Desktop\historical-war-sim\historical-war-sim\tools\unreal_bridge\`
2. Copy them into your project's Source folder:
   `[MyDocuments]/Unreal Projects/BattleSim/Source/BattleSim/`

### 🔧 Updating the Build Configuration
To allow Unreal to talk to WebSockets, you must update your `BattleSim.Build.cs` file (located in the same Source folder):
1. Find the `PublicDependencyModuleNames` line.
2. Update it to look like this:
```cpp
PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "WebSockets", "Json", "JsonUtilities" });
```

---

## 🏔️ STEP 4: Importing Historical Terrain

Unreal Landscapes use 16-bit heightmaps. I have generated your battle terrain for you.

1. Go to **Mode > Landscape** (Shift + 2) in the Unreal Editor.
2. Select **Import from File**.
3. Browse to the `ue5_heightmap.png` located in:
   `c:\Users\t3sfo\Desktop\historical-war-sim\historical-war-sim\backend\data\terrain\`
4. Click **Import**. You will now see the actual topography of the battlefield (Antietam/Gettysburg) in 3D.

---

## 🔫 STEP 5: Running the Live Simulation

1. Start your Python backend:
   `python backend/app/main.py`
2. In Unreal, drag the **WarSimWebSocketClient** component onto a Manager Actor.
3. Set the **BattleID** in the Details panel.
4. Press **Play**. You will now receive real-time updates from the Python engine!

---

> [!TIP]
> **Performance Scaling**
> The provided C++ code is optimized for 10,000 units. To visualize them, use the **Niagara System** or **Instanced Static Meshes** to avoid draw-call bottlenecks.

> [!IMPORTANT]
> **Help! My Project Won't Compile**
> If you see compilation errors, right-click the `.uproject` file in your Windows Explorer and select **"Generate Visual Studio project files"**, then try again.
