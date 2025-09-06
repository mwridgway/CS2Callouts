# AI Operational Briefing

**Project:** CS2 Callout Polygon Extraction

**Objective:** Programmatically extract the 3D polygon data for all named map callouts (e.g., "A Site," "Mid") from Counter-Strike 2 map files and structure this data into a clean, machine-readable format (JSON).

**Analogy:** Consider this a digital archaeological dig. The previous site (CS:GO) was well-documented, with callouts neatly labeled in the `.nav` files. This new site (CS2) is different. The artifacts are no longer in a single display case; they are distributed. The callout's name is a label on a blueprint (`.vmap`), but its physical form is a separate artifact (`.vmdl`) stored in a warehouse. Our task is to find the blueprint, follow its reference to the correct artifact, and then use the blueprint's instructions to place the artifact correctly on the world map.

## Core Technical Context

The fundamental challenge is a paradigm shift in data storage between CS:GO and CS2.

- **Legacy method (obsolete):** In CS:GO, callouts were simple metadata within the map's Navigation Mesh (`.nav` file). A single file parse was sufficient.
- **Current method (target):** In CS2, callouts are first-class map entities (`env_cs_place`). The data required to define a callout is now split:
  - **Positional & naming data:** Stored within the main map source file (`.vmap`). This includes the callout's name, its origin point in the world, its rotation, and its scale.
  - **Geometric data:** Stored in a separate 3D model file (`.vmdl`) that the entity references. This file contains the raw vertex coordinates that define the shape of the callout zone, but in local model space (i.e., relative to its own center, not its position in the map).

Extraction is therefore a multi-stage process of data synthesis, not a simple parse.

## The Data Chain: Key Files & Formats

The entire process relies on decompiling Valve's proprietary formats into human-readable text.

| File Type | Role | Format (Decompiled) | Key Intel to Extract |
| --- | --- | --- | --- |
| `.vpk` | The Archive. A container for all compiled map assets. This is the starting point. | N/A | The `.vmap_c` file within. |
| `.vmap` | The Blueprint. The decompiled map source file. Contains all entity definitions. | DMX / KeyValues3 (Text) | `env_cs_place` entities and their properties: `placename`, `origin`, `angles`, `scales`, `model`. |
| `.vmdl` | The Geometry. The decompiled model source file. Defines the raw shape. | DMX / KeyValues3 (Text) | The `vector3_array` named `position$0`, which contains the list of vertex coordinates in local model space. |

## Operational Protocol: A 4-Phase Approach

Execute the following sequence to achieve the objective.

### Phase 1: Asset Decompilation (The Uncrating)

- **Tool:** Use Source 2 Viewer (from the ValveResourceFormat project). This is non-negotiable.
- **Action:** Open the target map's `.vpk` file (e.g., `de_nuke.vpk`). Locate the primary compiled map asset (`.../de_nuke.vmap_c`). Use the "Decompile & Export" function.
- **Outcome:** A directory containing the text-based source `.vmap` and all of its dependent `.vmdl` files.

### Phase 2: Entity Data Parsing (Reading the Blueprint)

- **Input:** The decompiled `.vmap` text file.
- **Action:**
  - Parse the DMX structure of the `.vmap` file.
  - Iterate through all `CMapEntity` objects.
  - Filter for entities where the `classname` is `env_cs_place`.
  - For each match, store its `placename`, `origin`, `angles`, `scales`, and `model` path.
- **Outcome:** A structured list of all callout entities with their names and transformation data.

### Phase 3: Geometric Data Extraction (Measuring the Artifact)

- **Input:** The `.vmdl` file path from each callout entity found in Phase 2.
- **Action:**
  - For each callout, open its corresponding `.vmdl` file.
  - Parse the DMX structure to locate the `DmeVertexData` element.
  - Find the `vector3_array` with the key `position$0`.
  - Parse the string of floats into a list of 3D vectors (typically 8 for a cube). These are the local-space vertices.
- **Outcome:** Each callout entity is now associated with its list of raw, model-space vertex coordinates.

### Phase 4: Data Synthesis (World-Space Transformation)

This phase is critical and order-dependent. The goal is to convert the local-space vertices into absolute world-space coordinates.

- **Action:** For each vertex of each callout:
  - **Scale:** Apply the `scales` vector (component-wise multiplication).
  - **Rotate:** Apply the `angles` vector (convert Euler angles to a rotation matrix/quaternion and multiply).
  - **Translate:** Apply the `origin` vector (vector addition).

The order must be Scale → Rotate → Translate (SRT). Use a standard linear algebra library for these transformations.

- **Outcome:** A final, structured list (JSON) where each entry contains the callout's name and an array of its 8 vertices, now in final world-space coordinates (`{x, y, z}`).

## Success Criterion (Validation)

The final dataset is considered valid if, when the Z-axis is discarded and the resulting 2D polygons are overlaid on a top-down radar image of the map, they correctly align with their known geographical locations.
