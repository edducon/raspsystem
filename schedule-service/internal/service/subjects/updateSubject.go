package subjects

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *SubjectsService) UpdateSubject(subjectUUID string, subjectData *models.UpdateSubjectRequest) error {
	errUpdateSubject := s.repo.SubjectsRepository.UpdateSubject(subjectUUID, subjectData)

	if errUpdateSubject != nil {
		if errService.IsDuplicateError(errUpdateSubject) {
			return fmt.Errorf("failed to update subject: target subject already exists")
		}
		return fmt.Errorf("failed to update subject: %w", errUpdateSubject)
	}

	return nil
}
