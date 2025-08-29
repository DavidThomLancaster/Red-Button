from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form, Request
from Services.UserService import UserService
from Utils.AuthUtils import hash_password, get_user_id_from_header
from models.user_models import RegisterRequest, LoginRequest, CreateJobRequest, GetMapResp, PatchOpsReq
from models.contact_models import ContactSearchRequest, ContactSearchResponse, CreateContactBody
from models.email_batch_models import JobEmailBatchesDTO, BatchWithHeadersDTO, EmailBatchDTO, EmailHeaderDTO, EmailDetailsDTO, EmailUpdateDTO
from Utils.logger import get_logger
from Services.AuthService import AuthService
from Services.TokenService import TokenService
from Services.JobService import JobService
from Services.PromptService import PromptService
from Services.SchemaService import SchemaService
from Services.ContactService import ContactService
from pathlib import Path

from Repositories.UserRepository import UserRepository
from Repositories.JobRepository import JobRepository
from Repositories.PromptRepository import PromptRepository
from Repositories.ContactRepository import ContactRepository
from Repositories.EmailRepository import EmailRepository
from FileManager.FileManager import FileManager
from Core.core import Core
from shared.StorageRef import StorageMode
#from backend.shared.DTOs import ParamsDTO
from shared.DTOs import ContactDTO, ParamsDTO

from typing import List

log = get_logger(__name__)


router = APIRouter()

def get_user_service(request: Request) -> UserService:
    return UserService(request.app.state.user_repo)

def get_contacts_service(request: Request):
    return request.app.state.contact_svc  # already built in main.py

def get_job_service(request: Request) -> JobService:
    return JobService(
        request.app.state.job_repo,
        request.app.state.contact_repo,
        request.app.state.file_manager,
        request.app.state.core,
        request.app.state.prompt_svc,
        request.app.state.schema_svc,
        email_repo=request.app.state.email_repo,  # when you add it
    )

# def get_user_service():
#     user_repo = UserRepository()
#     return UserService(user_repo)

# def get_contacts_service():
#     contacts_repo = ContactRepository()
#     return ContactService(contacts_repo)


# def get_job_service():
#     prompt_rep = PromptRepository()
#     contacts_repo = ContactRepository()
#     prompt_service = PromptService(prompt_rep)
#     schema_service = SchemaService()
#     contacts_service = get_contacts_service()
#     job_repo = JobRepository()
#     file_manager = FileManager(mode=StorageMode.LOCAL)
#     core = Core(file_manager, contacts_service)
#     return JobService(job_repo, contacts_repo, file_manager, core, prompt_service, schema_service)

# Handlers

@router.get("/hello")
async def hello_world():
    
    return {"message": "Hello, world! Project slice is alive8 🚀"}

@router.get("/ping")
async def ping():
    return {"status": "ok"}

@router.post("/register")
async def register_user(request: RegisterRequest, user_service: UserService = Depends(get_user_service)):
    try:
        token = user_service.register_user(request.email, request.password)
        log.info("User registered successfully", extra={"user_email": request.email}) 
        #log.info(f"User ID: {user_id}")
        return {"access_token": token, "token_type": "bearer"}
        #return {"message": "User created successfully", "user_id": user_id}
    except HTTPException as e:
        log.warning("User registration failed", extra={"user_email": request.email, "reason": e.detail})
        raise
    except Exception as e:
        log.error("Unexpected error during user registration", exc_info=True, extra={"user_email": request.email})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error")
    

@router.post("/login")
async def login_user(request: LoginRequest, user_service: UserService = Depends(get_user_service)): 
    # TODO add more logging perhaps
    try:
        token = user_service.login(request.email, request.password)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
    # re-raise so FastAPI can return 401 properly
        raise
    except Exception as e:
        log.error("Unexpected error during user login", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    # returns results and does error handling

@router.post("/create_job")
async def create_job(request: CreateJobRequest, authorization: str = Header(...), job_service: JobService = Depends(get_job_service)):
    try:
        user_id = get_user_id_from_header(authorization)
        job_id = job_service.create_job(user_id, request.name, request.notes)
        return {"message": "Job created successfully", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error creating job", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get_job")
async def get_job(authorization: str = Header(...), job_service: JobService = Depends(get_job_service)):
    try:
        user_id = get_user_id_from_header(authorization)
        jobs = job_service.get_jobs(user_id)
        return {"jobs": jobs}
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error retrieving jobs", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/jobs/{job_id}")
async def get_job_details(job_id: str, authorization: str = Header(...), job_service: JobService = Depends(get_job_service)):
    try:
        # 1. Get the user ID from the auth header
        user_id = get_user_id_from_header(authorization)

        # 2. Fetch the job (and ensure it's owned by this user)
        job = job_service.get_job_by_id(user_id, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        # 3. Return job details
        return {"job": job}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unexpected error retrieving job {job_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/submit_pdf")
async def submit_pdf(authorization: str = Header(...), job_id: str = Form(...), pdf_file: UploadFile = File(), job_service: JobService = Depends(get_job_service)):
    try:
        user_id = get_user_id_from_header(authorization)
        safe_name = Path(pdf_file.filename).name  # strips directories
        # read file into bytes
        pdf_bytes = await pdf_file.read()

        ret = job_service.submit_pdf(user_id, job_id, pdf_bytes, safe_name)
        log.info(ret)
        return ret
    except Exception as e:
        log.error("Unexpected error submitting PDF", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, authorization: str = Header(...), job_service: JobService = Depends(get_job_service)):
    try:
        user_id = get_user_id_from_header(authorization)
        ret = job_service.delete_job(user_id, job_id)
        return ret  # { "status": "DELETED", "job_id": ... }
    except HTTPException:
        # pass through 404/403 from service
        raise
    except Exception:
        log.error("Unexpected error deleting job", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs/{job_id}/contacts-map", response_model=GetMapResp)
async def get_contacts_map(
    job_id: str,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    try:
        user_id = get_user_id_from_header(authorization)
        return job_service.get_contacts_map(user_id, job_id)    
    except HTTPException:
        # pass through 404/403 from service
        raise
    except Exception:
        log.error("Unexpected getting contacts map", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")    

@router.patch("/jobs/{job_id}/contacts-map")
async def patch_contacts_map(
    job_id: str,
    body: PatchOpsReq,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    try:
        user_id = get_user_id_from_header(authorization)
        log.info("Hey, the patch has been called. ")
        log.info(body.ops)
        log.info(body.base_ref)
        return job_service.apply_contacts_map_ops(user_id, job_id, body.base_ref, body.ops)
    except HTTPException:
        # pass through 404/403 from service
        raise
    except Exception:
        log.error("Unexpected error patching contacts map", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
   
@router.post("/generate_emails/{job_id}")
async def generate_emails(job_id: str, authorization: str = Header(...), job_service: JobService = Depends(get_job_service)):
    try:
        user_id = get_user_id_from_header(authorization)
        res = job_service.generate_emails(user_id, job_id)
        log.info(f"user_id: {user_id}, job_id: {job_id}")
        return res # This is the batch_id sent back to the client
    except Exception as e:
        log.error("Unexpected error generating emails", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# TODO Slice 7 - handler for getting contacts FIXME 
# FIXME - define request model for filters and pagination 
# wrap the parameters in an object probably.
@router.post("/jobs/{job_id}/contacts/search", response_model=ContactSearchResponse)
async def search_contacts(job_id: str, 
                          req: ContactSearchRequest, 
                          authorization: str = Header(...), 
                          contacts_service: ContactService = Depends(get_contacts_service),
                          job_service: JobService = Depends(get_job_service)):
    # Access filters like req.filters.trade, req.filters.q
    # Access pagination like req.page, req.page_size
    print("Reached the handler")
    print(req)
    try:
        user_id = get_user_id_from_header(authorization)
        params = ParamsDTO(
            user_id=user_id,
            trade=req.trade,
            name=req.name,
            service_area=req.service_area,
            limit=req.limit,
            page=req.page
        )
        result = contacts_service.get_contacts_by_parameters(params)
        return result
    except HTTPException:
        raise
    except Exception:
        log.error("Unexpected error searching contacts", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/my/contacts")
def create_my_contact(req: CreateContactBody, authorization: str = Header(...), contacts_service: ContactService = Depends(get_contacts_service)):
    user_id = get_user_id_from_header(authorization)
    print(req)
    return contacts_service.create_my_contact(user_id, req.model_dump())
    #return "Not implemented yet"

# TODO Slice 8 - handler for /get_batches_and_headers {token, job_id} => BatchesWithEmailHeadersResponse
@router.get("/jobs/{job_id}/email_batches", response_model=JobEmailBatchesDTO)
async def get_batches_and_headers(
    job_id: str,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    print("Reached the get_batches_and_headers handler")
    #return {"status": "ok"}
    try:
        user_id = get_user_id_from_header(authorization)
        aggregates = job_service.get_email_batches(user_id, job_id)  # List[BatchWithEmailHeaders]

        # Convert to DTOs for response
        batches_dto: List[BatchWithHeadersDTO] = []
        for agg in aggregates:
            batch_dto = EmailBatchDTO.from_orm(agg.batch)
            emails_dto = [EmailHeaderDTO.from_orm(e) for e in agg.emails]
            batches_dto.append(BatchWithHeadersDTO(batch=batch_dto, emails=emails_dto))

        return JobEmailBatchesDTO(job_id=job_id, batches=batches_dto)

    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error retrieving email batches and headers", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/delete_email/job/{job_id}/email/{email_id}")
async def delete_email(
    job_id: str,
    email_id: str,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    try:
        user_id = get_user_id_from_header(authorization)
        result = job_service.delete_email(user_id, job_id, email_id)
        return result  # { "status": "DELETED", "email_id": ... }
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error deleting email", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/delete_email_batch/job/{job_id}/batch/{batch_id}")
async def delete_email(
    job_id: str,
    batch_id: str,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    try:
        user_id = get_user_id_from_header(authorization)
        result = job_service.delete_email_batch(user_id, job_id, batch_id)
        return result  # { "status": "DELETED", "email_id": ... }
    except HTTPException:
        raise
    except Exception as e:
        log.error("Unexpected error deleting email batch", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/get_email_details/job/{job_id}/email/{email_id}", response_model=EmailDetailsDTO)
async def get_email_details(
    job_id: str,
    email_id: str,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service)
):
    try:
        log.info("Reached get_email_details handler")
        user_id = get_user_id_from_header(authorization)
        rec = job_service.get_email_details(user_id, job_id, email_id)  # EmailDetailsRecord (dataclass)

        # one-liner: validate from attributes of the dataclass
        return EmailDetailsDTO.model_validate(rec)

    except HTTPException:
        raise
    except Exception:
        log.error("Unexpected error retrieving email details", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.patch("/jobs/{job_id}/emails/{email_id}", response_model=EmailDetailsDTO)
async def patch_email(
    job_id: str,
    email_id: str,
    update: EmailUpdateDTO,
    authorization: str = Header(...),
    job_service: JobService = Depends(get_job_service),
):
    try:
        user_id = get_user_id_from_header(authorization)

        if not any([update.subject is not None, update.body is not None, update.to_email is not None, update.status is not None]):
            raise HTTPException(status_code=400, detail="No fields to update.")

        rec = job_service.update_email(
            user_id, job_id, email_id,
            subject=update.subject,
            body=update.body,
            to_email=update.to_email,
            status=update.status,
        )
        if rec is None:
            # either not found, wrong job, or not editable (e.g., already sent)
            raise HTTPException(status_code=409, detail="Email not editable or not found.")

        # DTO from dataclass
        return EmailDetailsDTO.model_validate(rec)

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        log.error("Unexpected error updating email", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
   


# @router.post("/create_job")
# async def create_job(request: CreateJobRequest, authorization: str = Header(...)): 
#     try:
#         # 1. Extract token from header
#         if not authorization.startswith("Bearer "):
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Invalid authorization header format")
#         token = authorization.split(" ")[1]

#         # 2. Validate & decode
#         payload = TokenService.validate_token(token)
#         if not payload:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Invalid or expired token")

#         log.info("Token was validated!", extra={"nope": 1})

#         # 3. Extract user_id
#         user_id = payload.get("user_id")
#         if not user_id:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Token missing user_id")

#         # 4. Create the job
#         job_id = JobService.create_job(user_id, request.name, request.notes)

#         log.info("Job created", extra={"user_id": user_id, "job_id": job_id})
#         return {"message": "Job created successfully", "job_id": job_id}

#     except HTTPException:
#         raise
#     except Exception as e:
#         log.error("Unexpected error creating job", exc_info=True, extra={"request": request.dict()})
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Internal server error")

# @router.get("/get_job")
# async def get_job(authorization: str = Header(...)):
#     try:
#         # 1. Extract token from header
#         if not authorization.startswith("Bearer "):
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Invalid authorization header format")
#         token = authorization.split(" ")[1]

#         # 2. Validate & decode
#         payload = TokenService.validate_token(token)
#         if not payload:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Invalid or expired token")

#         log.info("Token was validated!", extra={"endpoint": "get_job"})

#         # 3. Extract user_id (using "sub" if that’s how you set it)
#         user_id = payload.get("user_id")
#         if not user_id:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Token missing user_id")

#         # 4. Get jobs for this user
#         jobs = JobService.get_jobs(user_id)

#         log.info("Jobs retrieved", extra={"user_id": user_id, "job_count": len(jobs)})
#         return {"jobs": jobs}

#     except HTTPException:
#         raise
#     except Exception as e:
#         log.error("Unexpected error retrieving jobs", exc_info=True, extra={"authorization": authorization})
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Internal server error")

# FOR TESTING PURPOSES - Can we push this to github?
