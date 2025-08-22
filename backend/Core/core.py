from shared.StorageRef import StorageRef, StorageMode
from pathlib import Path
import fitz
import base64
import math
from dotenv import load_dotenv
load_dotenv()
import os
import io
import openai
import csv
import json
import hashlib
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional, Iterable, Tuple

from collections import defaultdict
from FileManager.FileManager import FileManager
from Services.ContactService import ContactService
from Utils.logger import get_logger
log = get_logger(__name__)

api_key = os.getenv("OPENAI_API_KEY")

class Core:
    def __init__(self, file_manager, contact_service: ContactService):
        self.file_manager = file_manager
        self.client = openai.OpenAI(api_key=api_key)
        self.contact_service = contact_service

    def extract_images(self, user_id, job_id, pdf_ref, start_page: int | None = None, end_page: int | None = None) -> StorageRef:
        log.info("Extracting images from PDF", extra={"user_id": user_id, "job_id": job_id})
        pdf_path = self.file_manager.load_file(pdf_ref)
        pdf_path = Path(pdf_path)

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")
        
        num_pages = len(doc)
        #print(f"PDF loaded with {num_pages} page")

        # Handle defaults
        if start_page is None:
            start_page = 1
        if end_page is None:
            end_page = num_pages

        # Validate range
        if start_page < 1 or end_page > num_pages or start_page > end_page:
            raise ValueError(
                f"Invalid page range: {start_page}–{end_page} for {num_pages} pages."
            )

        # 1. Get the path or location of the folder where you're storing the images (user_id, job_id)
        images_ref = self.file_manager.get_images_dir(user_id, job_id)
        # 2. Go through all the images and then tell the file manager to save them (user_id, job_id)
        image_counter = 0
        for page_num in range(start_page - 1, end_page):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)
            filename = f"page_{page_num + 1}.png"

            img_bytes = pix.tobytes("png")
            self.file_manager.save_image(user_id, job_id, filename, img_bytes)
            #print(f"Saved image: {filename}")
            image_counter += 1

        doc.close()
        # 3. After you do all that, return that path that you generated based on (user_id, job_id) in a StorageRef that has the mode. 
        log.debug("Extracted %s images", image_counter)
        return images_ref
    

    def run_llm_on_images(self, user_id, job_id, images_ref, prompt, batch_size):
        log.info("Running LLM on images", extra={"user_id": user_id, "job_id": job_id, "batch_size": batch_size})
        # 0. Get the location 

        # 1. User File manager to get the images
        image_files = self.file_manager.get_image_files(images_ref)

        # 2. Make ref for the CSV files folder
        csvs_ref = self.file_manager.get_csvs_dir(user_id, job_id)


        #print("\n\n" + str(image_files) + "\n\n")
        # 3. Go through things in batches
        batch_counter = 0
        num_batches = math.ceil(len(image_files) / batch_size)
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = start_idx + batch_size
            batch_files = image_files[start_idx:end_idx]
            
            content_blocks = [{"type": "text", "text": prompt}]
            for filename in batch_files:
                image_path = self.file_manager.get_image_path(images_ref, filename)
                #print("\n\n" + str(image_path) + "\n\n")
                with open(image_path, "rb") as img_f:
                    image_data = base64.b64encode(img_f.read()).decode()
                page_number = filename.replace("page_", "").replace(".png", "")
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                })
                content_blocks.append({"type": "text", "text": f"(This is page {page_number}.)"})

            #print("\n\nPreview of content blocks:\n", self.preview_content_blocks(content_blocks), "\n\n")

            # 4. Sumbit to the LLM
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": content_blocks}]
                )
            except Exception as e:
                continue

            #print(response)
            
            # 4.2 Get the csv_content
            csv_content = response.choices[0].message.content

            # 4.3 Clean the csv_content
            if csv_content.startswith("```"):
                csv_content = csv_content.strip().lstrip("`").replace("```csv", "").replace("```", "").strip()
            lines = [line.strip() for line in csv_content.splitlines() if line.strip()]

            # 4.4 Write the CSV files using magic
            # Save CSV with FileManager
            batch_filename = f"batch_{batch_num + 1}.csv"
            csv_bytes = io.StringIO()
            writer = csv.writer(csv_bytes)

            for line in lines:
                try:
                    reader = csv.reader(io.StringIO(line))
                    for row in reader:
                        if len(row) >= 3:
                            writer.writerow([cell.strip() for cell in row])
                        else:
                            log.error("\n\nERROR in core.py len of row is < 3\n" + row)
                            #print("\n\nERROR in core.py len of row is < 3")
                            #print(row)
                            # emit(Fore.YELLOW + "WARNING" + Fore.RESET,
                            #      f" Skipping malformed row in batch {batch_num + 1}: {line}")
                except Exception as e:
                    #print("ERROR in core.py exception")
                    log.error("ERROR in core.py exception")
                    # emit(Fore.RED + "ERROR" + Fore.RESET,
                    #      f" CSV parse error: {str(e)} on line: {line}")

            csv_path = self.file_manager.save_csv(user_id, job_id, batch_filename,
                                                  csv_bytes.getvalue().encode("utf-8"))
            #csv_paths.append(csv_path)

            # emit(Fore.BLUE + "INFO" + Fore.RESET,
            #      f"  Saved batch {batch_num + 1} to {csv_path}")
            batch_counter += 1

        # 5. User File manager to save those Csv files to the right place
        # 6. ReturnRef with the CSV files location and other meta data

        log.debug("Generated CSV batches", extra={"batch_count": batch_counter})
    

        return csvs_ref
    
    def combine_to_json(self, user_id, job_id, csvs_ref):
        # TODO
        log.info("Running combine_to_json", extra={"user_id": user_id, "job_id": job_id})
        # Get a directory from the file manager where you can put these files...
        json_ref = self.file_manager.get_json_dir(user_id, job_id) # TODO - Implement me CHECK
        # get the files from the CSV ref
        csv_files = self.file_manager.get_csv_files(csvs_ref) # TODO - Me too! CHECK
        # make sure the CSV files exist
        if not csv_files:
            # TODO - raise some kind of error or something here CHECK
            raise FileNotFoundError(f"No CSV files found for job {job_id} at {csvs_ref.location}")
        # Go through the files and add them to a dict
        combined_data = defaultdict(list)
        for file_name in csv_files:
            file_path = self.file_manager.get_csv_path_by_file_name(csvs_ref, file_name) # TODO - implement me CHECK
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if len(row) < 3:
                        #emit(Fore.YELLOW + "WARNING" + Fore.RESET, f"Skipping malformed row in {file_name}: {row}")
                        # TODO - some kind of error here
                        continue

                    trade = row[0].strip()
                    pages_str = row[1].strip()
                    note = ",".join(row[2:]).strip()

                    page_list = [p.strip() for p in pages_str.split(",") if p.strip()]
                    combined_data[trade].append({
                        "note": note,
                        "pages": page_list
                    })
        # Save this as a json using the file manager
        self.file_manager.save_json(json_ref, combined_data) # TODO - implement me CHECK
        # return the reference generated by the file manager
        return json_ref

    def normalize_json(self, user_id, job_id, jsons_ref, schema_text):
        log.info("Normalizing JSON", extra={"user_id": user_id, "job_id": job_id})
        # 3. Use FileManager to get combined.json from file from jsons_ref
        combined_json_str = self.file_manager.get_combined_json(jsons_ref) # this is a string...
        combined_json = json.loads(combined_json_str)

        # 4 Now for the main algorithm
        schema = json.loads(schema_text)
        alias_map = {}
        for trade in schema.get("trades", []):
            name = trade["name"]
            alias_map[name.lower()] = name
            for alias in trade.get("aliases", []):
                alias_map[alias.lower()] = name

        normalized = {}
        undefined = []

        for raw_name, entries in combined_json.items():
            raw_key = raw_name.lower()
            if raw_key in alias_map:
                norm_key = alias_map[raw_key]
                #emit(Fore.LIGHTGREEN_EX + "PROGRESS" + Fore.RESET, f"Normalized '{raw_name}' → '{norm_key}'")
                if norm_key not in normalized:
                    normalized[norm_key] = []
                normalized[norm_key].extend(entries)
            else:
                #emit(Fore.YELLOW + "WARNING" + Fore.RESET, f"Unrecognized trade '{raw_name}' → added to 'undefined'")
                for entry in entries:
                    undefined.append({
                        "original_name": raw_name,
                        "note": entry.get("note", ""),
                        "pages": entry.get("pages", [])
                    })

        # Add undefined to normalized result if any
        if undefined:
            normalized["undefined"] = undefined

        
        # 4) Ensure every entry has contacts: []
        for trade, items in normalized.items():
            for item in items:
                # normalize shape
                item["note"] = item.get("note", "")
                item["pages"] = [str(p) for p in item.get("pages", [])]
                item.setdefault("contacts", [])

        # Step 3: Sort for consistency
        normalized_json = dict(sorted(normalized.items(), key=lambda x: x[0].lower()))

        # 6) Add metadata (provenance + pipeline state)
        #now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        #combined_hash = hashlib.sha256(combined_json_str.encode("utf-8")).hexdigest()
        normalized_json["metadata"] = {
            "processing_steps": ["normalized"],
            "job": {
                "user_id": user_id,
                "job_id": job_id,
            },
        }

        # Step 4: Save output
        normalized_json_ref = self.file_manager.save_normalized_json(jsons_ref, normalized_json)
        return normalized_json_ref

    def map_contacts(self, jsons_ref: str, limit_per_section: int | None = None):
        data = json.loads(self.file_manager.get_normalized_json(jsons_ref))
        for trade, items in data.items():
            if trade == "metadata": continue
            ids = self.contact_service.get_contact_ids_for_trade(trade, limit_per_section)
            for item in items: item["contacts"] = ids
        meta = data.setdefault("metadata", {})
        meta.setdefault("processing_steps", []).append("contacts_mapped")
        #meta["last_updated_at"] = datetime.utcnow().isoformat(timespec="seconds")+"Z"
        ref = self.file_manager.save_latest_json(jsons_ref, data)
        return ref
    

    # ---------------- main ----------------

    def generate_emails(self, job_id: str, template: dict,
                    email_repo, contacts_map_ref) -> str:
        # 1. Load contacts map
        contacts_map = self.file_manager.load_json(contacts_map_ref)

        # 2. Create batch
        batch_id = email_repo.create_batch(
            job_id=job_id,
            contacts_map_ref=str(contacts_map_ref),
            template_version=template.get("version", "v1"),
            template_ref=None  # wire in later if needed
        )

        # 3. Loop over trades
        for trade, scopes in contacts_map.items():
            if trade == "metadata":
                continue

            # pick override or default template
            override = template.get("overrides", {}).get(trade, {})
            subject_template = override.get("subject", template["subject"])
            body_template = override.get("body", template["body"])

            # 4. Loop over scopes for this trade
            for scope in scopes:
                note = scope.get("note", "")
                pages = ", ".join(scope.get("pages", []))
                contact_ids = scope.get("contacts", [])

                if not contact_ids:
                    continue

                # fetch all contacts at once
                contacts = self.contact_service.contact_repo.get_contacts_by_ids(contact_ids)

                # 5. Loop over resolved contacts
                for contact in contacts:
                    name = contact.get("name") or "there"
                    to_email = contact.get("email")
                    if not to_email:
                        log.warning(f"Contact {contact['id']} missing email, skipping")
                        continue

                    # format email
                    subject = subject_template.format(
                        name=name, trade=trade, pages=pages, notes=note
                    )
                    body = body_template.format(
                        name=name, trade=trade, pages=pages, notes=note
                    )

                    # save email
                    email_repo.create_email(
                        batch_id=batch_id,
                        job_id=job_id,
                        contact_id=contact["id"],
                        to_email=to_email,
                        subject=subject,
                        body=body
                    )

        return batch_id


    def preview_content_blocks(self, blocks):
        preview = []
        for b in blocks:
            if b["type"] == "image_url":
                preview.append({
                    "type": "image_url",
                    "image_url": {"url": "<base64 image data omitted>"}
                })
            else:
                preview.append(b)
        return preview

