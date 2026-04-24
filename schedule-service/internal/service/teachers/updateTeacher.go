package teachers

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *TeachersService) UpdateTeacher(teacherUUID string, teacherData *models.UpdateTeacherRequest) error {
	if teacherData.FirstName == "" {
		return fmt.Errorf("failed to update teacher: first name required")
	} else if teacherData.SecondName == "" {
		return fmt.Errorf("failed to update teacher: second name required")
	}

	errUpdateTeacher := s.repo.TeachersRepository.UpdateTeacher(teacherUUID, teacherData)

	if errUpdateTeacher != nil {
		if errService.IsDuplicateError(errUpdateTeacher) {
			return fmt.Errorf("failed to update teacher: target teacher already exists")
		}
		return fmt.Errorf("failed to update teacher: %w", errUpdateTeacher)
	}

	return nil
}
