# CS2 Callouts - Development Roadmap

## 🎯 Phase 2: Production Enhancement & Multi-Map Support

### ✅ **Completed (Phase 1)**
- [x] Multi-VPK extraction pipeline
- [x] 23/23 callouts extracted for de_mirage  
- [x] Perfect awpy coordinate transformation
- [x] Radar overlay visualization
- [x] Cross-platform Python CLI
- [x] Documentation complete
- [x] **BONUS: Full 3D polygon data extraction** (physics mesh integration)

---

## 🚀 **Next Phase Objectives**

### 🎨 **1. Enhanced Visualization - Callout Area Rendering**
**Priority: HIGH** | **Status: ✅ COMPLETED**

**Current State**: Full polygon area rendering with radar overlay support  
**Target**: ✅ **ACHIEVED** - Render the actual 2D polygon areas on the radar

- [x] **Implement polygon area rendering** instead of just origin points
  - [x] Use `matplotlib.patches.Polygon` for filled areas
  - [x] Add semi-transparent polygon fills to show coverage zones
  - [x] Maintain current label positioning at polygon centroids
  - [x] Add outline/border styling options

- [x] **Enhanced styling options**
  - [x] Configurable fill colors per callout (deterministic pastel colors)
  - [x] Adjustable transparency for area vs border emphasis (`--alpha` option)
  - [x] Color coding by callout type (hash-based color assignment)
  - [x] Professional styling presets (customizable linewidth, labels, transparency)

**Available Commands:**
```bash
# Basic polygon visualization
python -m cs2_callouts visualize --json out/de_mirage_callouts.json --out out/polygons.png

# Radar overlay with polygon areas
python -m cs2_callouts visualize --json out/de_mirage_callouts.json \
  --radar ~/.awpy/maps/de_mirage.png --map-data map-data.json \
  --out out/radar_overlay.png --alpha 0.3 --linewidth 1.5 --labels
```

**Deliverable**: ✅ **COMPLETED** - Radar images showing actual callout coverage areas with perfect pixel alignment

---

### 📦 **2. Coordinate Export System**
**Priority: CRITICAL** | **Status: TODO**

**Purpose**: Enable integration with external CS2 analysis projects

- [ ] **Multi-format export support**
  - [ ] JSON format (current) - enhanced with metadata
  - [ ] CSV format for spreadsheet analysis
  - [ ] Python pickle format for direct import
  - [ ] XML format for legacy system compatibility
  - [ ] awpy-compatible format for seamless integration

- [ ] **Enhanced coordinate data**
  - [ ] World coordinates (current)
  - [ ] Radar pixel coordinates  
  - [ ] Normalized coordinates (0-1 range)
  - [ ] Bounding box data (min/max X/Y)
  - [ ] Area calculations (polygon area in game units)
  - [ ] Centroid coordinates

- [ ] **Export command implementation**
  ```bash
  python -m cs2_callouts export --map de_mirage --format json,csv,awpy --out exports/
  ```

**Deliverable**: Clean, documented coordinate data for external project integration

---

### 🗺️ **3. Multi-Map Automation**
**Priority: HIGH** | **Status: TODO**

**Current State**: Manual single-map processing  
**Target**: Automated processing for all Active Duty maps

- [ ] **Active Duty map detection**
  - [ ] Automatic CS2 installation scanning
  - [ ] Active Duty map list maintenance
  - [ ] Map availability validation

- [ ] **Batch processing pipeline**
  ```bash
  python -m cs2_callouts batch --maps active_duty --formats json,awpy
  python -m cs2_callouts batch --maps all --radar-overlay
  ```

- [ ] **Current Active Duty Maps (2025)**
  - [ ] **de_mirage** ✅ (completed)
  - [ ] **de_dust2** 
  - [ ] **de_inferno**
  - [ ] **de_nuke** 
  - [ ] **de_vertigo**
  - [ ] **de_ancient**
  - [ ] **de_anubis**

- [ ] **Progress tracking & reporting**
  - [ ] Extraction success/failure logging
  - [ ] Missing VPK file detection
  - [ ] Callout count validation per map
  - [ ] Automated quality assurance checks

**Deliverable**: Complete callout database for all competitive CS2 maps

---

### 📸 **4. Documentation & Examples**
**Priority: MEDIUM** | **Status: TODO**

- [ ] **README enhancement**
  - [ ] Add example rendered image (de_mirage radar overlay)
  - [ ] Usage examples for external projects
  - [ ] API documentation for coordinate data
  - [ ] Integration guide for awpy ecosystem

- [ ] **Example gallery**
  - [ ] Create `examples/` directory
  - [ ] Generate radar overlays for all Active Duty maps
  - [ ] Different styling examples (analysis vs presentation)
  - [ ] Before/after comparison images

- [ ] **Developer documentation**
  - [ ] Coordinate system explanation with diagrams
  - [ ] Integration examples with popular CS2 analysis tools
  - [ ] Performance benchmarks and optimization tips

**Deliverable**: Professional documentation with visual examples

---

### 🔧 **5. Automated CI/CD Pipeline**
**Priority: MEDIUM** | **Status: TODO**

**Target**: GitHub Actions for automated builds and releases

- [ ] **Build automation**
  - [ ] Automated testing on Windows/Linux/macOS
  - [ ] Python package building and validation
  - [ ] Cross-platform compatibility testing

- [ ] **Release automation**
  - [ ] Automatic version tagging
  - [ ] PyPI package publishing
  - [ ] Release notes generation
  - [ ] Asset packaging (VRF CLI, example data)

- [ ] **Quality assurance**
  - [ ] Automated callout extraction testing
  - [ ] Coordinate accuracy validation
  - [ ] Performance regression testing
  - [ ] Documentation link checking

- [ ] **GitHub Actions workflow**
  ```yaml
  # .github/workflows/build.yml
  - Build and test on matrix of Python versions
  - Validate extraction on sample maps
  - Generate and upload example visualizations
  - Deploy to PyPI on tagged releases
  ```

**Deliverable**: Fully automated build, test, and release pipeline

---

## 📋 **Implementation Priority Order**

### **Sprint 1: Core Functionality** (Estimated: 1-2 weeks)
1. ✅ **COMPLETED** - Polygon area rendering in visualization
2. ✅ Enhanced export system with multiple formats
3. ✅ Basic multi-map processing capability

### **Sprint 2: Scale & Automation** (Estimated: 2-3 weeks)  
4. ✅ Complete Active Duty map processing
5. ✅ Batch processing commands
6. ✅ Quality assurance and validation

### **Sprint 3: Polish & Distribution** (Estimated: 1-2 weeks)
7. ✅ Documentation with examples and images
8. ✅ GitHub Actions CI/CD pipeline
9. ✅ Release preparation and packaging

---

## 🎯 **Success Metrics**

- [ ] **Coverage**: 7/7 Active Duty maps processed successfully
- [ ] **Quality**: >95% callout extraction success rate across all maps
- [ ] **Performance**: <2 minutes per map for complete pipeline
- [ ] **Usability**: One-command batch processing for all maps
- [ ] **Integration**: Export formats compatible with major CS2 analysis tools
- [ ] **Reliability**: Automated testing ensures consistent results

---

## 🚀 **Future Considerations (Phase 3)**

- **Real-time integration**: Live demo parsing for callout position analysis
- **3D visualization**: Interactive 3D callout zone display
- **Community maps**: Support for workshop and community map callouts
- **API service**: Web API for callout data access
- **Mobile compatibility**: Lightweight exports for mobile analysis apps

---

*Last Updated: September 6, 2025*  
*Current Status: Phase 1 Complete ✅ | Phase 2 Ready to Begin 🚀*
