from pathlib import Path
from shared.StorageRef import StorageRef, StorageMode
import os
import json
import uuid
from typing import Any

class FileManager:

    def __init__(self, mode: StorageMode, base_dir: str = "storage"):
        self.mode = mode
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_job_folder(self, user_id: str, job_id: str) -> Path:
        job_path = self.base_dir / f"user_{user_id}" / f"job_{job_id}"
        job_path.mkdir(parents=True, exist_ok=True)
        return job_path

    def save_pdf(self, user_id: str, job_id: str, pdf_bytes: bytes, filename: str = "input.pdf") -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            path = self._make_path(user_id, job_id, "pdfs", filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf_bytes)
            location = str(path.relative_to(self.base_dir))
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet.")
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")

        return StorageRef(location=location, mode=self.mode)




    def save_image(self, user_id: str, job_id: str, filename: str, image_bytes: bytes) -> str:
        path = self._make_path(user_id, job_id, "images", filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image_bytes)
        return str(path.relative_to(self.base_dir))

    def save_csv(self, user_id: str, job_id: str, filename: str, csv_bytes: bytes) -> str:
        path = self._make_path(user_id, job_id, "csvs", filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(csv_bytes)
        return str(path.relative_to(self.base_dir))

    def load_file(self, ref: StorageRef) -> bytes:
        if ref.mode == StorageMode.LOCAL:
            path = self.base_dir / ref.location
            return str(path)#.read_bytes()
        elif ref.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet.")
        else:
            raise ValueError(f"Unsupported mode {ref.mode}")

    def _make_path(self, user_id: str, job_id: str, subdir: str, filename: str) -> Path:
        return self.base_dir / f"user_{user_id}" / f"job_{job_id}" / subdir / filename
    
    
    def get_images_dir(self, user_id: str, job_id: str) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / f"user_{user_id}" / f"job_{job_id}" / "images"
            dir_path.mkdir(parents=True, exist_ok=True)
            location = str(dir_path.relative_to(self.base_dir))
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet. get_images_dir()")
            # In S3, we return a prefix, not a physical folder
            #location = f"user_{user_id}/job_{job_id}/images/"
            # Optionally ensure the "folder" exists by writing a placeholder object
            # self.s3_client.put_object(Bucket=self.bucket, Key=location, Body=b"")
        
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")

        return StorageRef(location=location, mode=self.mode)
    
    
    def get_csvs_dir(self, user_id: str, job_id: str) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / f"user_{user_id}" / f"job_{job_id}" / "csvs"
            dir_path.mkdir(parents=True, exist_ok=True)
            location = str(dir_path.relative_to(self.base_dir))
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet. get_images_dir()")
            # In S3, we return a prefix, not a physical folder
            #location = f"user_{user_id}/job_{job_id}/images/"
            # Optionally ensure the "folder" exists by writing a placeholder object
            # self.s3_client.put_object(Bucket=self.bucket, Key=location, Body=b"")
        
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")

        return StorageRef(location=location, mode=self.mode)
    
    def get_json_dir(self, user_id, job_id):
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / f"user_{user_id}" / f"job_{job_id}" / "json"
            dir_path.mkdir(parents=True, exist_ok=True)
            location = str(dir_path.relative_to(self.base_dir))
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet. get_json_dir()")
            # In S3, we return a prefix, not a physical folder
            #location = f"user_{user_id}/job_{job_id}/images/"
            # Optionally ensure the "folder" exists by writing a placeholder object
            # self.s3_client.put_object(Bucket=self.bucket, Key=location, Body=b"")
        
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")

        return StorageRef(location=location, mode=self.mode)
    
    def get_image_files(self, images_ref : StorageRef):
        if self.mode == StorageMode.LOCAL:
            path = path = self.base_dir / images_ref.location
            print("\n\n" + str(path) + "\n\n")
            image_files = sorted([
                f for f in os.listdir(path)
                if f.lower().endswith(".png")
            ], key=lambda x: int(x.replace("page_", "").replace(".png", "")))
            if not image_files:
                raise FileNotFoundError(f"No .png files found in {path}")
            return image_files
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(f"S3 storage mode is not implemented yet. get_image_files()")
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def get_csv_files(self, csvs_ref: StorageRef):
        if self.mode == StorageMode.LOCAL:
            path = self.base_dir / csvs_ref.location
            csv_files = sorted([
                f for f in os.listdir(path)
                if f.lower().endswith(".csv")
            ])
            if not csv_files:
                raise FileNotFoundError(f"No .csv files found in {path}")
            return csv_files

        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. get_csv_files()"
            )
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def get_combined_json(self, jsons_ref: StorageRef) -> str:
        if self.mode == StorageMode.LOCAL:
            path = self.base_dir / jsons_ref.location / "combined.json"
            if not path.exists():
                raise FileNotFoundError(f"Combined JSON not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        elif self.mode == StorageMode.S3:
            raise NotImplementedError("S3 storage mode is not implemented yet: get_combined_json()")
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def get_normalized_json(self, jsons_ref: StorageRef) -> str:
        if self.mode == StorageMode.LOCAL:
            path = self.base_dir / jsons_ref.location / "normalized.json"
            if not path.exists():
                raise FileNotFoundError(f"Combined JSON not found: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        elif self.mode == StorageMode.S3:
            raise NotImplementedError("S3 storage mode is not implemented yet: get_normalized_json()")
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def get_csv_path_by_file_name(self, csvs_ref: StorageRef, file_name: str):
        if self.mode == StorageMode.LOCAL:
            path = self.base_dir / csvs_ref.location / file_name
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {path}")
            return path

        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. get_csv_path_by_file_name()"
            )
        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")

    

    def save_json(self, json_ref: StorageRef, combined_data: dict) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / json_ref.location
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / "combined.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2)
            #return StorageRef(location=str(file_path), mode=self.mode)
            relative_path = file_path.relative_to(self.base_dir)
            return StorageRef(location=str(relative_path), mode=self.mode)
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. save_json()"
            )

        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    #user_id, job_id, cmap, fname
    def save_json_as(self, user_id, job_id, cmap, fname) -> StorageRef: #json_ref: StorageRef, combined_data: dict) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / f"user_{user_id}" / f"job_{job_id}" / "json"
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / fname
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cmap, f, indent=2)
            #return StorageRef(location=str(file_path), mode=self.mode)
            relative_path = file_path.relative_to(self.base_dir)
            return StorageRef(location=str(relative_path), mode=self.mode)
        
        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. save_json_as()"
            )

        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def save_normalized_json(self, combined_json_ref, normalized_json) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / combined_json_ref.location
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / "normalized.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(normalized_json, f, indent=2)
            relative_path = dir_path.relative_to(self.base_dir)
            return StorageRef(location=str(relative_path), mode=self.mode)

        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. save_json()"
            )

        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")
        
    def save_latest_json(self, combined_json_ref, the_json) -> StorageRef:
        if self.mode == StorageMode.LOCAL:
            dir_path = self.base_dir / combined_json_ref.location
            dir_path.mkdir(parents=True, exist_ok=True)

            if isinstance(the_json, str):
                try:
                    the_json = json.loads(the_json)
                except json.JSONDecodeError as e:
                    raise ValueError(f"save_latest_json expected dict/list or JSON string; got invalid JSON: {e}")


            # Generate unique filename for latest version
            filename = f"latest_{uuid.uuid4().hex}.json"
            file_path = dir_path / filename

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(the_json, f, indent=2)

            relative_path = file_path.relative_to(self.base_dir)
            return StorageRef(location=str(relative_path), mode=self.mode)

        elif self.mode == StorageMode.S3:
            raise NotImplementedError(
                "S3 storage mode is not implemented yet. save_latest_json()"
            )

        else:
            raise ValueError(f"Unsupported storage mode: {self.mode}")


        
    def get_image_path(self, images_ref: StorageRef, image_name):
        return self.base_dir / images_ref.location / image_name
        # I should stub out the S3 version here, but I don't want to right now TODO

    def _resolve_path(self, location: str | Path) -> Path:
        p = Path(location)
        return p if p.is_absolute() else (self.base_dir / p).resolve()


    def load_json(self, ref: StorageRef) -> dict | list:
        mode = getattr(ref, "mode", None)
        if mode in (StorageMode.LOCAL, "local", None):
            # resolve against base_dir
            path = (self.base_dir / ref.location) if not os.path.isabs(ref.location) else Path(ref.location)
            path = Path(path).resolve()
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # If the file contained a JSON string, parse it
            if isinstance(data, str):
                return json.loads(data)
            return data

        raise ValueError(f"Unsupported storage mode for load_json: {mode}")


    # def load_json(self, ref: StorageRef) -> dict:
    #     mode = getattr(ref, "mode", None)
    #     if mode in (StorageMode.LOCAL, "local", None):
    #         path = self._resolve_path(ref.location)
    #         if not path.exists():
    #             raise FileNotFoundError(f"JSON not found: {path} (cwd={os.getcwd()})")
    #         with path.open("r", encoding="utf-8") as f:
    #             return json.load(f)
    #     raise ValueError(f"Unsupported storage mode for load_json: {mode}")



    # def load_json(self, ref: StorageRef) -> dict:
    #     mode = getattr(ref, "mode", None)
    #     if mode in (StorageMode.LOCAL, "local", None):
    #         with open(ref.location, "r", encoding="utf-8") as f:
    #             return json.load(f)
    #     # TODO: handle s3, etc.
    #     raise ValueError(f"Unsupported storage mode for load_json: {mode}")
