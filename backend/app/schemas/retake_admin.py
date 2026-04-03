from pydantic import BaseModel, ConfigDict, Field


class PastSemesterImportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_path: str | None = Field(default=None, validation_alias="sourcePath", serialization_alias="sourcePath")


class PastSemesterImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    source_path: str = Field(serialization_alias="sourcePath")
    imported_records: int = Field(serialization_alias="importedRecords")
    unique_groups: int = Field(serialization_alias="uniqueGroups")
    unique_subjects: int = Field(serialization_alias="uniqueSubjects")
    message: str


class RetakeResetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    deleted_retakes: int = Field(serialization_alias="deletedRetakes")
    deleted_teacher_links: int = Field(serialization_alias="deletedTeacherLinks")
    message: str
