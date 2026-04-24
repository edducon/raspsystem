package subjects

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *SubjectsService) DeleteSubject(subjectUUID string) error {
	err := s.repo.SubjectsRepository.DeleteSubject(subjectUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete subject: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("subject not found: %w", err)
		}
		return err
	}

	return nil
}
