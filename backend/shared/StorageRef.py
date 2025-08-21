from dataclasses import dataclass
from enum import Enum

class StorageMode(Enum):
    LOCAL = "local"
    S3 = "s3" # add these later
    GCS = "gcs" # add these latter... if at all...

@dataclass
class StorageRef:
    location: str
    mode: StorageMode
