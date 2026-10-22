from pydantic import BaseModel, Field


class PageParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def paginate(query, params: PageParams):
    return query.limit(params.limit).offset(params.offset).all()
