package subjects

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *SubjectsService) CreateSubject(subjectReqData *models.AddSubjectRequest) (string, error) {
	subjectUUID := uuid.NewString()

	Subject := &models.Subject{
		UUID: subjectUUID,
		Name: subjectReqData.Name,
	}

	errCreateSubject := s.repo.SubjectsRepository.CreateSubject(Subject)

	if errCreateSubject != nil {
		if errService.IsDuplicateError(errCreateSubject) {
			return "", fmt.Errorf("failed to create subject: subject already exists")
		}
		return "", fmt.Errorf("failed to create subject: %w", errCreateSubject)
	}

	return subjectUUID, nil
}
