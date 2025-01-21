from pydantic import BaseModel

class PypiPackage(BaseModel):
    name: str
    version: str
    description: str