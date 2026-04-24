package teachers

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *TeachersService) DeleteTeacher(teacherUUID string) error {
	err := s.repo.TeachersRepository.DeleteTeacher(teacherUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete teacher: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("teacher not found: %w", err)
		}
		return err
	}

	return nil
}
