package subjectTypes

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *SubjectTypesService) CreateSubjectType(subjectTypeReqData *models.AddSubjectTypeRequest) (string, error) {
	subjectTypeUUID := uuid.NewString()

	SubjectType := &models.SubjectType{
		UUID: subjectTypeUUID,
		Type: subjectTypeReqData.Type,
	}

	errCreateSubjectType := s.repo.SubjectTypesRepository.CreateSubjectType(SubjectType)

	if errCreateSubjectType != nil {
		if errService.IsDuplicateError(errCreateSubjectType) {
			return "", fmt.Errorf("failed to create subject type: subject type already exists")
		}
		return "", fmt.Errorf("failed to create subject type: %w", errCreateSubjectType)
	}

	return subjectTypeUUID, nil
}
