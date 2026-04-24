package subjectTypes

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *SubjectTypesService) UpdateSubjectType(subjectTypeUUID string, subjectTypeData *models.UpdateSubjectTypeRequest) error {
	errUpdateSubjectType := s.repo.SubjectTypesRepository.UpdateSubjectType(subjectTypeUUID, subjectTypeData)

	if errUpdateSubjectType != nil {
		if errService.IsDuplicateError(errUpdateSubjectType) {
			return fmt.Errorf("failed to update subject type: target subject type already exists")
		}
		return fmt.Errorf("failed to update subject type: %w", errUpdateSubjectType)
	}

	return nil
}
