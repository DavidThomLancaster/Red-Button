from Repositories.JobRepository import JobRepository
from Repositories.ContactRepository import ContactRepository
from FileManager import FileManager  # adjust import path if needed
from fastapi import HTTPException, status
from starlette import status as http_status
from pathlib import Path
from shared.StorageRef import StorageRef, StorageMode
from Services.PromptService import PromptService
from Services.SchemaService import SchemaService
import json
from Utils.logger import get_logger
import hashlib
from typing import Optional, Dict, List, Literal
from datetime import datetime

log = get_logger(__name__)

class JobService:
    def __init__(self, job_repo: JobRepository, contacts_repo: ContactRepository, file_manager: FileManager, core, prompt_service: PromptService, schema_service: SchemaService):
        self.job_repo = job_repo
        self.contacts_repo = contacts_repo
        self.file_manager = file_manager
        self.core = core
        self.prompt_service = prompt_service
        self.schema_service = schema_service

    def create_job(self, user_id: str, job_name: str, notes: str) -> str:
        try:
            job_id = self.job_repo.insert_new_job(user_id, job_name, notes)
            # Create folder structure for this job
            self.file_manager.create_job_folder(user_id, job_id)
            log.info("Created job folder", extra={"user_id": user_id, "job_id": job_id})
            return job_id
        except Exception as e:
            log.error("Failed to create job", exc_info=True, extra={"user_id": user_id, "job_name": job_name})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create job"
            ) from e

    def get_jobs(self, user_id: str):
        try:
            return self.job_repo.get_jobs_by_user(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve jobs"
            ) from e
        
    
    def get_job_by_id(self, user_id, job_id):
        job = self.job_repo.get_job(job_id)
        if job is None:
            return None
        # Ensure this job belongs to the requesting user
        if job["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return dict(job)  # or transform to desired API shape
    
    def delete_job(self, user_id: str, job_id: str) -> dict:
        owner = self.job_repo.get_owner_id(job_id)
        if owner is None:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Job not found")
        if owner != user_id:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this job")

        #ok = self.job_repo.delete_job(job_id, soft=True)
        ok = self.job_repo.delete_job_hard(job_id)
        if not ok:
            # Row existed but update/delete affected 0 rows (race condition?) 
            raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job")

        return {"status": "DELETED", "job_id": job_id}
    
    def _ref_to_dict(self, ref):
        if ref is None:
            return None
        # If your StorageRef has to_dict(), use it; otherwise make a minimal dict
        if hasattr(ref, "to_dict"):
            return ref.to_dict()
        return {"mode": getattr(ref, "mode", None), "location": getattr(ref, "location", None)}


    def _split_map_and_metadata(self, data: dict) -> tuple[dict, dict | None]:
        if not isinstance(data, dict):
            return {}, None
        meta = data.get("metadata")
        cleaned = {k: v for k, v in data.items() if k != "metadata" and isinstance(v, list)}
        return cleaned, meta

    def get_contacts_map(self, user_id: str, job_id: str) -> dict:
        self._assert_owner(user_id, job_id)
        job = self.job_repo.get_job_by_id(job_id)
        if not job:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Job not found")

        src_ref = self._load_source_map_ref(job)
        raw = self.file_manager.load_json(src_ref)

        cmap, meta = self._split_map_and_metadata(raw)
        ids = self._collect_contact_ids(cmap)
        contacts = self._resolve_contacts(ids)

        # optional: normalize path to forward slashes for FE portability
        from pathlib import Path
        ref_str = Path(src_ref.location).as_posix()

        return {
            "status": "OK",
            "job_id": job_id,
            "ref": ref_str,
            "map": cmap,
            "contactsById": contacts,
            "metadata": meta,
        }  
    

    def _canon_ref(self, s: str) -> str:
        # normalize separators + trim
        return s.replace("\\", "/").strip()


    def apply_contacts_map_ops(self, user_id: str, job_id: str, base_ref: str, ops: list) -> dict:
        self._assert_owner(user_id, job_id)

        # Compare refs in a platform-agnostic way
        current_ref_raw = self.job_repo.get_contacts_map_ref(job_id) or self.job_repo.get_jsons_ref(job_id)
        current_ref = self._canon_ref(current_ref_raw or "")
        base_ref = self._canon_ref(base_ref or "")

        if not current_ref or current_ref != base_ref:
            raise HTTPException(http_status.HTTP_409_CONFLICT, "Map changed; refresh and try again")

        # Normalize ops to dicts (supports Pydantic models)
        norm_ops = []
        for op in ops:
            if hasattr(op, "model_dump"):
                norm_ops.append(op.model_dump())
            elif hasattr(op, "dict"):
                norm_ops.append(op.dict())
            elif isinstance(op, dict):
                norm_ops.append(op)
            else:
                raise HTTPException(http_status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unsupported op type: {type(op).__name__}")

        # Load current map (full doc, may include "metadata")
        cmap = self.file_manager.load_json(StorageRef(location=current_ref_raw, mode=StorageMode.LOCAL))

        # Apply ops
        for op in norm_ops:
            trade = op["trade"]; idx = op["block"]; cid = str(op["contact_id"])
            blocks = cmap.get(trade, [])
            if not isinstance(blocks, list) or idx < 0 or idx >= len(blocks):
                raise HTTPException(http_status.HTTP_400_BAD_REQUEST, f"Invalid block index for trade '{trade}'")

            block = blocks[idx] if isinstance(blocks[idx], dict) else {}
            # ensure the block has a contacts list we can mutate
            contacts = block.setdefault("contacts", [])
            if not isinstance(contacts, list):
                contacts = block["contacts"] = [str(contacts)]

            if op["op"] == "add_contact":
                if cid not in contacts:
                    contacts.append(cid)
            elif op["op"] == "remove_contact":
                block["contacts"] = [x for x in contacts if str(x) != cid]
            else:
                raise HTTPException(http_status.HTTP_400_BAD_REQUEST, f"Unknown op '{op['op']}'")

            # write back block in case it was not a dict originally
            blocks[idx] = block
            cmap[trade] = blocks

        # Save new version (keep entire doc, including metadata)
        fname = f"contacts_map_{datetime.utcnow().isoformat().replace(':','-')}.json"
        new_ref = self.file_manager.save_json_as(user_id, job_id, cmap, fname)
        self.job_repo.update_status_contacts_map(job_id, new_ref)

        # Clean response map: only trades with list blocks (strip metadata/strays)
        cleaned_map = {k: v for k, v in cmap.items() if k != "metadata" and isinstance(v, list)}

        # Resolve contacts for FE convenience
        ids = self._collect_contact_ids(cleaned_map)
        contacts = self._resolve_contacts(ids)

        return {
            "status": "UPDATED",
            "ref": Path(new_ref.location).as_posix(),
            "map": cleaned_map,
            "contactsById": contacts,
            # optionally also return "metadata": cmap.get("metadata"),
        }

    # def apply_contacts_map_ops(self, user_id: str, job_id: str, base_ref: str, ops: list[dict]) -> dict:
    #     self._assert_owner(user_id, job_id)
    #     current_ref = self.job_repo.get_contacts_map_ref(job_id) or self.job_repo.get_jsons_ref(job_id)
    #     current_ref  = self._canon_ref(current_ref or "")
    #     base_ref = self._canon_ref(base_ref or "")

    #     print("\n\ncur_norm:", current_ref, "\nbase_norm:", base_ref, "\n\n")
    #     if not current_ref or current_ref != base_ref:
    #         raise HTTPException(http_status.HTTP_409_CONFLICT, "Map changed; refresh and try again")
    #     print("\n\n You should see this text if exception not raised\n\n")
    #     cmap = self.file_manager.load_json(StorageRef(location=current_ref, mode=StorageMode.LOCAL))  # adapt
    #     for op in ops:
    #         trade = op.trade; idx = op.block; cid = op.contact_id
    #         blocks = cmap.get(trade, [])
    #         if idx < 0 or idx >= len(blocks):
    #             raise HTTPException(http_status.HTTP_400_BAD_REQUEST, f"Invalid block index for trade '{trade}'")
    #         contacts = blocks[idx].get("contacts", [])
    #         if op.op == "add_contact":
    #             if cid not in contacts:
    #                 contacts.append(cid)
    #         elif op.op == "remove_contact":
    #             contacts[:] = [x for x in contacts if x != cid]

    #     # Save new version
    #     fname = f"contacts_map_{datetime.utcnow().isoformat().replace(':','-')}.json"
    #     new_ref = self.file_manager.save_json_as(user_id, job_id, cmap, fname) # TODO - Needs to be save json as...
    #     self.job_repo.update_status_contacts_map(job_id, new_ref) 
    #     # Respond with resolved contacts so UI can update names immediately
    #     ids = self._collect_contact_ids(cmap)
    #     contacts = self._resolve_contacts(ids)
    #     return {"status": "UPDATED", "ref": new_ref.location, "map": cmap, "contactsById": contacts}

    # TODO complete this...
    def submit_pdf(self, user_id: str, job_id: str, pdf_file: bytes, safe_name):
        # ---------------------------------- SAVING THE PDF ----------------------------------------
        log.info("Submitting PDF", extra={"user_id": user_id, "job_id": job_id, "pdf_filename": safe_name})
        pdf_ref: StorageRef = self.file_manager.save_pdf(user_id, job_id, pdf_file, safe_name)
        self.job_repo.update_status_pdf_saved(job_id, pdf_ref)
        log.debug("PDF saved", extra={"pdf_ref": pdf_ref.location})

        # ---------------------------------- EXTRACTING IMAGES --------------------------------------
        # call core.extract_images(pdf_ref) # the function uses the file manager to save the images. It just gets injected. 
        # updates teh status with the reference to where the images are stored. 
        images_ref = self.core.extract_images(user_id, job_id, pdf_ref, 7, 10) # TODO - complete implementation. 7 and 10 are just place holders...
        self.job_repo.update_status_images_extracted(job_id, images_ref)
        log.debug("Images extracted", extra={"images_ref": images_ref.location})

        # ---------------------------------- SUBMITTING TO THE LLM ----------------------------------------
        # get prompt from fileManager
        prompt, prompt_ref_string = self.prompt_service.get_active_prompt()
        log.debug("Retrieved active prompt")
        #print("\n\n" + prompt + "\n\n")

        # call core.run_llm_on_images(images_ref, prompt_ref) # The core will probably have to use the file manager to extract data from those references and save the csvs
        csvs_ref = self.core.run_llm_on_images(user_id, job_id, images_ref, prompt, 10) # maybe I need more settings here

        # update the status to show that the csv is complete it returns the reference to where the CSVs are stored.
        
        self.job_repo.update_status_llm_run(job_id, csvs_ref, prompt_ref_string)
        log.info("LLM run complete", extra={"csv_ref": csvs_ref.location})
        # update the prompt here instead of before. 


        # ---------------------------------- SAVING CSVS TO COMBINED.JSON ----------------------------------------
        log.info("Saving CSVs to combined.JSON")
        combined_json_ref = self.core.combine_to_json(user_id, job_id, csvs_ref) 
        print(combined_json_ref.location)
        
        # ---------------------------------- NORMALIZING JSON FILE TO NORMALIZED.JSON ----------------------------------------
        log.info("Normalizing Json file")
        schema_text, schema_ref = self.schema_service.get_active_schema() 
        normalized_json_ref = self.core.normalize_json(user_id, job_id, combined_json_ref, schema_text) 
        self.job_repo.update_status_json_normalized(job_id, normalized_json_ref, schema_ref) 

        # ---------------------------------- BUILD THE CONTACT MAP ----------------------------------------
        log.info("Creating Default Contacts Map")
        contacts_map_ref = self.core.map_contacts(normalized_json_ref) 
        self.job_repo.update_status_contacts_map(job_id, contacts_map_ref) 

        contacts_map = self.file_manager.get_normalized_json(normalized_json_ref)
        
        
        return {
            "status": "CONTACT_MAP_READY",
            "pdf_ref": self._ref_to_dict(pdf_ref),
            "images_ref": self._ref_to_dict(images_ref),
            "contacts_map_ref": self._ref_to_dict(contacts_map_ref),
            "contacts_map": contacts_map  # <-- frontend reads this directly
        }

        # return {"contacts_map_ref": contacts_map_ref}

    # --- HELPER FUNCTIONS ---

    def _assert_owner(self, user_id: str, job_id: str):
        owner = self.job_repo.get_owner_id(job_id)
        if owner is None:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Job not found")
        if owner != user_id:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, "Not authorized")
   
    def _resolve_contacts(self, ids: List[str]) -> Dict[str, dict]:
        if not ids:
            return {}
        unique = sorted(set(ids))
        rows = self.contacts_repo.get_contacts_by_ids(unique)  # returns list of dicts
        return {r["id"]: r for r in rows}
    
    def _load_source_map_ref(self, job_row: dict):
        # Prefer current mapped map; otherwise fall back to normalized json if it already contains contacts arrays
        ref = job_row.get("current_mapped_contacts_ref") or job_row.get("jsons_ref")
        if not ref:
            raise HTTPException(http_status.HTTP_409_CONFLICT, "No contact map available yet")
        return StorageRef(location=ref, mode=StorageMode(job_row.get("jsons_mode") or "local"))

    def _collect_contact_ids(self, cmap: dict) -> list[str]:
        """
        Collect unique contact IDs from a contact map shaped like:
        { "<Trade>": [ {note, pages, contacts:[...]}, ... ], "metadata": {...} }

        - Skips the `metadata` key.
        - Accepts contacts as list or single value.
        - Returns IDs as strings, preserving first-seen order.
        """
        ids: list[str] = []
        seen: set[str] = set()

        for trade, blocks in cmap.items():
            if trade == "metadata":
                continue
            if not isinstance(blocks, list):
                continue

            for b in blocks:
                # blocks should be dicts, but be forgiving
                if isinstance(b, dict):
                    contacts = b.get("contacts", [])
                else:
                    contacts = []

                # normalize contacts to a list
                if isinstance(contacts, (str, int)):
                    contacts = [contacts]
                elif not isinstance(contacts, list):
                    contacts = []

                for cid in contacts:
                    cid_str = str(cid).strip()
                    if cid_str and cid_str not in seen:
                        seen.add(cid_str)
                        ids.append(cid_str)

        return ids


    # def _collect_contact_ids(self, cmap: dict) -> List[str]:
    #     ids = []
    #     for blocks in cmap.values():
    #         for b in blocks:
    #             ids.extend(b.get("contacts", []))
    #     return ids