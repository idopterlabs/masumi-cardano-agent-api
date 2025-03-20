import asyncio
import dotenv
import hashlib
import logging
import os
import uuid
import uvicorn
from database import get_db, Job
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session


dotenv.load_dotenv(override=True)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from masumi.config import Config
from masumi.payment import Payment, Amount

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MASUMI_PAYMENT_SERVICE_URL = os.getenv("MASUMI_PAYMENT_SERVICE_URL")
MASUMI_PAYMENT_API_KEY = os.getenv("MASUMI_PAYMENT_API_KEY")
MASUMI_AGENT_ID = os.getenv("MASUMI_AGENT_ID")
SELLING_WALLET_VKEY = os.getenv("SELLING_WALLET_VKEY")

config = Config(
    payment_service_url=MASUMI_PAYMENT_SERVICE_URL,
    payment_api_key=MASUMI_PAYMENT_API_KEY
)

app = FastAPI(title="Masumi AI Agent", description="An AI Agent available on the Masumi Network")

class JobRequest(BaseModel):
    input: str


# This is the function that actually performs the task.
# It is called by the handle_payment_status function after payment confirmation.
async def execute_job(job_input: str) -> None:
    """ Executes job after payment confirmation """
    
    # 👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇
    #!!!! Run your agent code here
    # result = YourAIAgent.run(job_input)
    
    print(f"\n\nExecuting job with input: {job_input} !!!\n\n")

    # Just simulating the time it takes the Agent to execute the job
    # Remove this line in your own implementation
    await asyncio.sleep(10)

    # return the result of running the agent
    return "Finished executing Job and this is the result"

# This is the function that handles the payment status once payment is confirmed.
# It is called by the start_job function after payment confirmation.
async def handle_payment_status(job_id: uuid.UUID) -> None:
    """ Handles payment confirmation and invokes function to execute the job """
    db = next(get_db())
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        print(f"Job {job_id} not found")
        return "Job not found"

    job.status = "running"
    db.commit()

    # Execute the AI task
    result = await execute_job(job.input_data)

    # Convert result to string if it's not already
    result_str = str(result)
    
    # Creates a hash of the result to be submitted to the payment service
    # and will eventually be stored on-chain
    result_hash = hashlib.sha256(result_str.encode()).hexdigest()

    # Rebuilds the payment object to be used to complete the payment
    payment = Payment(
        agent_identifier=MASUMI_AGENT_ID,
        amounts=[Amount(amount=job.cost, unit="lovelace")],
        config=config,
        identifier_from_purchaser=job.identifier_from_purchaser
    )

    # Completes the payment and submits the result hash to the payment service
    await payment.complete_payment(job.payment_id, result_hash)

    # Refresh the job object from the database after commit
    db.refresh(job)

     # Update job status
    job.status = "completed"
    job.payment_status = "completed"
    job.result = result
    job.result_hash = result_hash
    db.commit()

    # Stop monitoring payment status
    payment.stop_status_monitoring()

@app.post('/start_job')
async def start_job(request: JobRequest, db: Session = Depends(get_db)):
    job_id = uuid.uuid4()

    # Creates a hash of the input to be used as the identifier from the purchaser
    # Trims the result to 25 characters to follow payment service requirements
    identifier_from_purchaser = hashlib.sha256(request.input.encode()).hexdigest()[:25]
    # This cost can be arbitrary. 
    # Using a default of 10 ADA.
    cost_in_lovelace = "10000000"
    # Define payment amounts
    amounts = [Amount(amount=cost_in_lovelace, unit="lovelace")]  # 10 tADA as example
    
    # Create a payment request using Masumi
    payment = Payment(
        agent_identifier=MASUMI_AGENT_ID,
        amounts=amounts,
        config=config,
        identifier_from_purchaser=identifier_from_purchaser,
        input_data=request.input
    )

    payment_request = await payment.create_payment_request()
    payment_id = payment_request["data"]["blockchainIdentifier"]
    input_hash = payment_request["data"]["inputHash"]

    # Creates a job object to be used to store the job in the database
    # so that it can be retrieved and updated after payment confirmation
    # as well as returned from the /status endpoint
    job = Job(
        id=job_id, 
        cost=cost_in_lovelace,
        payment_id=payment_id, 
        status="pending", 
        payment_status="pending", 
        input_data=request.input, 
        input_hash=input_hash,
        identifier_from_purchaser=identifier_from_purchaser
    )
    db.add(job)
    db.commit()

    # Defines a function that will be called when the payment status changes
    async def payment_callback(payment_id: str):
        await handle_payment_status(job_id)

    # Starts monitoring the payment status passing the callback function
    # that will be called when the payment status changes
    await payment.start_status_monitoring(payment_callback)

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "job_id": str(job_id),
            "blockchainIdentifier": payment_request["data"]["blockchainIdentifier"],
            "submitResultTime": payment_request["data"]["submitResultTime"],
            "unlockTime": payment_request["data"]["unlockTime"],
            "externalDisputeUnlockTime": payment_request["data"]["externalDisputeUnlockTime"],
            "agentIdentifier": MASUMI_AGENT_ID,
            "sellerVkey": SELLING_WALLET_VKEY,
            "identifierFromPurchaser": identifier_from_purchaser,
            "Amounts": [{"amount": amount.amount, "unit": amount.unit} for amount in amounts],
            "inputHash": input_hash
        }
    )

@app.get('/status')
async def status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
    if not job:
        content = {
            "status": "error",
            "message": "Job not found"
        }
        return JSONResponse(status_code=404, content=content)

    content = {
        "job_id": str(job.id),
        "status": job.status,
        "payment_status": job.payment_status,
        "result": job.result
    }
    return JSONResponse(status_code=200, content=content)
        

if __name__ == "__main__":
    print("Starting FastAPI server with Masumi integration...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    ## Debugging
    ## set UUID for the job to debug
    # job_uuid = """
    # db = next(get_db())
    # job = db.query(Job).filter(Job.id == uuid.UUID(job_uuid)).first()
    # print(f"Job ID: {job.id}")
    # print(f"Status: {job.status}")
    # print(f"Payment Status: {job.payment_status}")
    # print(f"Cost: {job.cost}")
    # print(f"Result: {job.result}")
    # print(f"Input: {job.input_data}")
    # print(f"Identifier from purchaser: {job.identifier_from_purchaser}")
    # print(f"Result hash: {job.result_hash}")
