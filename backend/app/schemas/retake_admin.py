from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PastSemesterImportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_path: Annotated[str | None, Field(default=None, validation_alias="sourcePath", serialization_alias="sourcePath")]


class PastSemesterImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    source_path: Annotated[str, Field(serialization_alias="sourcePath")]
    imported_records: Annotated[int, Field(serialization_alias="importedRecords")]
    unique_groups: Annotated[int, Field(serialization_alias="uniqueGroups")]
    unique_subjects: Annotated[int, Field(serialization_alias="uniqueSubjects")]
    message: str


class RetakeResetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    deleted_retakes: Annotated[int, Field(serialization_alias="deletedRetakes")]
    deleted_teacher_links: Annotated[int, Field(serialization_alias="deletedTeacherLinks")]
    message: str