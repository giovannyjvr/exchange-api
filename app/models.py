from pydantic import BaseModel, Field

class QuoteOut(BaseModel):
    sell: float
    buy: float
    date: str
    id_account: str = Field(..., alias="id-account")

    class Config:
        populate_by_name = True
        orm_mode = True
