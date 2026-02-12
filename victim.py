from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class DivideInput(BaseModel):
    a: int
    b: int
    
    class Config:
        # Ensure OpenAPI schema is generated correctly
        schema_extra = {
            "example": {
                "a": 10,
                "b": 2
            }
        }

@app.post("/divide")
def divide(data: DivideInput):
    # This will crash with 500 when b=0
    return {"result": data.a // data.b}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)