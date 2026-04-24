package subjectTypes

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *SubjectTypesService) DeleteSubjectType(subjectTypeUUID string) error {
	err := s.repo.SubjectTypesRepository.DeleteSubjectType(subjectTypeUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete subject type: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("subject type not found: %w", err)
		}
		return err
	}

	return nil
}
