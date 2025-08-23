from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form, Request
from Services.UserService import UserService
from Utils.AuthUtils import hash_password, get_user_id_from_header
from models.user_models import RegisterRequest, LoginRequest, CreateJobRequest, GetMapResp, PatchOpsReq
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
        user_id = user_service.register_user(request.email, request.password)
        log.info("User registered successfully", extra={"user_email": request.email}) 
        return {"message": "User created successfully", "user_id": user_id}
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
        return res # TODO
    except Exception as e:
        log.error("Unexpected error generating emails", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



