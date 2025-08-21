import json
from shared.StorageRef import StorageRef, StorageMode

class SchemaService:
    def __init__(self):
        self.temp_schema = """
        {
  "schema_version": "2025-08-06",
  "trades": [
    {
      "name": "Plumbing",
      "aliases": ["Plumber", "Water Lines", "Sanitary Sewer", "Piping", "Stormwater Management", "Site Development", "Civil/Grading"],
      "description": "Handles piping, fixtures, and waste systems."
    },
    {
      "name": "Electrical",
      "aliases": ["Electrician", "Power", "Lighting"],
      "description": "Installs wiring, panels, and lighting systems."
    },
    {
      "name": "HVAC",
      "aliases": ["Mechanical", "Ventilation", "Heating", "Air Conditioning"],
      "description": "Installs climate control systems."
    },
    {
      "name": "Surveying",
      "aliases": ["Land Surveyor"],
      "description": "Establishes boundaries and control points on the site."
    },
    {
      "name": "Demolition",
      "aliases": ["Demo", "Site Demo"],
      "description": "Removes existing structures and prepares for new construction."
    }
  ]
}
        """.strip()
        
        self.temp_schema_ref = StorageRef(location="HARDCODED IN SCHEMASERVICE", mode=StorageMode.LOCAL)

    def get_active_schema(self):
        return self.temp_schema, self.temp_schema_ref
