# Source 2 Transformation System

## Key Discovery: Scale vs. Global Scale in Source 2

Based on research into Source 2 engine transformation system, there are distinct differences between the various transformation properties we extract from GLB physics models:

### Transformation Types

#### 1. Scale (Local/Interactive)
- **Definition**: Standard scaling applied in Hammer editor or via transformation matrices
- **Function**: Changes object dimensions along local axes (X, Y, Z)
- **Scope**: Local to the object's coordinate system
- **Application**: Can be applied interactively and modified after model compilation
- **In Our Data**: The `scale` property from GLB transformation matrices (typically 0.0254 for inch-to-meter conversion)

#### 2. Rotation
- **Definition**: Object orientation manipulation around pivot points
- **Function**: Spins object around X, Y, or Z axes
- **Scope**: Can be local (around object origin) or global (around relocated pivot)
- **Application**: Interactive in editor, doesn't affect object scale
- **In Our Data**: The `rotation` property from GLB transformation matrices

#### 3. Global Scale (Compiled/Permanent)
- **Definition**: Engine-level scaling defined via `$scale` command in model compilation
- **Function**: Uniform scaling factor applied to entire model during compilation
- **Scope**: Permanent base scale for the model
- **Application**: Set once during model compilation, affects all instances
- **In Our Data**: The `global_scale` property derived from GLB vertex bounds - represents the model's actual tactical area dimensions

### Transformation Order: Scale → Rotate → Translate (SRT)

The order of operations is critical in 3D graphics:
1. **Scale**: Apply local scaling transformations
2. **Rotate**: Apply rotational transformations  
3. **Translate**: Apply positional transformations

This ensures transformations are applied correctly relative to object position and orientation.

### Implications for CS2 Callout Extraction

#### What We Extract:
- **`scale`**: Local transformation scale (0.0254 inch-to-meter conversion factor)
- **`rotation`**: Object orientation in 3D space
- **`global_scale`**: Actual tactical area dimensions from compiled model

#### Why This Matters:
1. **Individual Physics Properties**: Each callout model has unique global scale dimensions that represent actual gameplay areas
2. **Proper Scaling**: Our global scale multiplier system respects the compiled model dimensions
3. **Coordinate Accuracy**: Understanding SRT order ensures correct world space transformations

### Example from Our Data:
```json
{
  "name": "Scaffolding",
  "physics_properties": {
    "scale": [0.0254, 0.0254, 0.0254],      // Local scale (inch-to-meter)
    "rotation": [0.0, 0.0, 0.0],            // Object orientation
    "global_scale": [5.08, 8.74, 2.81]     // Compiled model dimensions (tactical area)
  }
}
```

### Technical Implementation:
- **GLB Loading**: Extracts transformation matrices and vertex bounds
- **Physics Properties**: Distinguishes between local scale and global dimensions
- **Polygon Scaling**: Uses global scale for tactical area representation
- **Global Multiplier**: Applies uniform scaling while preserving individual proportions

This understanding validates our approach of using `global_scale` for polygon dimensions rather than the local `scale` factor, ensuring callout areas match actual gameplay reality.
