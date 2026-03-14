from pydantic import BaseModel


class ImproviseContext(BaseModel):
    role: str = ""
    company: str = ""
    section_type: str = "experience"


class ImproviseRequest(BaseModel):
    text: str
    context: ImproviseContext = ImproviseContext()


class ImproviseResponse(BaseModel):
    improved_text: str
    alternatives: list[str] = []
