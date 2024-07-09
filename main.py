import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from GCvision import detect_features
from dotenv import load_dotenv
from typing import Dict, Any
from fastapi.openapi.utils import get_openapi

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Include the auth router
app.include_router(auth_router, prefix="/auth", tags=["auth"])


# Configure CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/detect-features", response_model=Dict[str, Any], responses={200: {"description": "Success"}, 400: {"description": "Bad Request"}, 500: {"description": "Internal Server Error"}})
async def detect_features_endpoint(file: UploadFile = File(...), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    
    try:
        logging.debug(f"Received file: {file.filename}")

        # Check if file is an image
        if not file.content_type.startswith('image'):
            logging.error(f"Uploaded file is not an image: {file.content_type}")
            raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

        # Save the uploaded file locally
        file_location = f"uploads/{file.filename}"
        with open(file_location, 'wb') as f:
            content = await file.read()
            f.write(content)

        logging.debug(f"File saved at: {file_location}")

        # Detect features using the function from vs.py
        detection_results = detect_features(file_location)

        logging.debug(f"Detection results: {detection_results}")

        # Determine the status and response based on detection results
        response_content = {
            "Status": 200,
            "information": {
                "message": "Detection completed.",
                "file_name": file.filename,
                "detection_results": {}
            }
        }

        if detection_results["speedometer"]:
            response_content["information"]["detection_results"] = "Speedometer Image"
        elif detection_results["vehicle_exterior"]:
            response_content["information"]["detection_results"] = {
                "vehicle_exterior": "Vehicle Exterior Image",
                "color": detection_results["color"]
            }

        return JSONResponse(status_code=200, content=response_content)
    except Exception as e:
        logging.error(f"Error in detect_features_endpoint: {e}")
        return JSONResponse(status_code=500, content={
            "Status": 500,
            "information": {
                "message": "Internal Server Error",
                "file_name": file.filename if 'file' in locals() else None
            }
        })

# Custom OpenAPI schema function to include OAuth2 security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API with JWT authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/login",
                    "scopes": {}
                }
            }
        }
    }
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
