# 🧹 Audience Engine Codebase Refactoring Plan

## 📊 Current State Analysis

**Current Structure:** 
- 12 services files (many redundant)
- 9 route files (many small/underused)  
- 7 documentation files (overlapping content)
- 4 ingestion scripts (similar functionality)
- Files: ~40+ → Target: ~20

## 🎯 Consolidation Strategy

### 1. 📁 File Structure Cleanup

#### Documentation Consolidation (7 → 1)
```bash
# REMOVE these redundant docs:
rm ADDING_CITIES_GUIDE.md
rm BIRMINGHAM_LIVERPOOL_INTEGRATION.md  
rm FRONTEND_INTEGRATION_SUMMARY.md
rm GLASSMORPHISM_AUDIENCE_UPDATE.md
rm COMPACT_AUDIENCE_GRID_UPDATE.md
rm MANCHESTER_INTEGRATION_SUMMARY.md
rm CITY_DATA_README.md

# UPDATE: Merge all content into README.md
```

#### Ingestion Scripts (4 → 1)
```bash
# REMOVE redundant scripts:
rm ingest_city_data.py
rm import_from_json.py  
rm migrate_city_data.py

# RENAME and enhance:
mv ingest_multiple_cities.py tools/city_ingestion.py
```

### 2. 🔧 Services Consolidation

#### A. Merge Persona Services
**Target:** `persona.py` + `persona_service.py` → `persona_service.py`

**Issues Found:**
- `persona.py` has broken syntax (undefined variables)
- Duplicate OpenAI configuration
- Overlapping functionality

```python
# NEW: src/services/persona_service.py
# Combines both files, fixes issues, single responsibility
```

#### B. Consolidate Data Services  
**Target:** `ons_data_service.py` + `city_audience_service.py` + `client_data_service.py` → `data_service.py`

**Rationale:**
- All handle data retrieval/processing
- Similar patterns and dependencies
- Can share connection pooling

```python
# NEW: src/services/data_service.py
class DataService:
    def __init__(self):
        self.ons_data = ONSDataHandler()
        self.city_data = CityDataHandler() 
        self.client_data = ClientDataHandler()
```

#### C. Merge AI Utilities
**Target:** `summary.py` + `vision.py` → `ai_service.py`

**Rationale:**
- Both are thin wrappers around OpenAI
- Can share model configuration
- Natural grouping

### 3. 📝 Routes Consolidation

#### Small Routes → `api.py`
```python
# MERGE these small routes into src/routes/api.py:
- presets.py (21 lines)
- history.py (19 lines) 
- client_data.py (23 lines)
- test_content.py (15 lines)
- audience.py (32 lines)
- summary.py (31 lines)
- analyze.py (51 lines)

# KEEP separate:
- focus_group.py (328 lines - main functionality)
- city_data.py (106 lines - specialized)
```

### 4. 📋 Implementation Steps

#### Phase 1: Safe Documentation Cleanup
1. Consolidate all docs into README.md
2. Remove redundant markdown files
3. Update any references

#### Phase 2: Services Refactoring
1. **Fix persona.py syntax issues**
2. **Merge persona services** 
3. **Create consolidated data_service.py**
4. **Update imports in app.py**

#### Phase 3: Routes Consolidation  
1. **Create unified api.py route**
2. **Migrate small routes**
3. **Update blueprint registration**

#### Phase 4: Tools Organization
1. **Move ingestion to tools/ directory**
2. **Remove redundant scripts**
3. **Update documentation**

## 🎯 Expected Benefits

### File Reduction
- **Before:** ~40 files
- **After:** ~20 files  
- **Reduction:** 50%

### Maintenance Benefits
- ✅ Easier to navigate
- ✅ Fewer imports to manage
- ✅ Consistent patterns
- ✅ Reduced duplication

### Developer Experience
- ✅ Single source of truth for docs
- ✅ Logical service grouping
- ✅ Simplified testing
- ✅ Clearer dependencies

## ⚠️ Implementation Notes

### Critical Fixes Required
1. **Fix `src/services/ons_data_service.py` indentation error**
2. **Fix `src/services/persona.py` syntax issues**
3. **Update all import statements**

### Testing Strategy
1. Keep existing tests during refactoring
2. Run tests after each phase
3. Update test imports as needed

### Deployment Considerations
- No breaking changes to API endpoints
- Frontend remains unchanged
- Database schema unchanged
- Environment variables unchanged

## 🚀 Quick Wins (Can do immediately)

1. **Remove documentation files** (low risk)
2. **Fix syntax errors** (critical)
3. **Remove unused ingestion scripts** (low risk)
4. **Organize tools/ directory** (low risk)

Would you like me to start with any specific phase? 