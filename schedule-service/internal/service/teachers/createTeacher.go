package teachers

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *TeachersService) CreateTeacher(teacherReqData *models.AddTeacherRequest) (string, error) {
	if teacherReqData.FirstName == "" {
		return "", fmt.Errorf("failed to create teacher: first name required")
	} else if teacherReqData.SecondName == "" {
		return "", fmt.Errorf("failed to create teacher: second name required")
	}

	teacherUUID := uuid.NewString()

	Teacher := &models.Teacher{
		UUID:       teacherUUID,
		FirstName:  teacherReqData.FirstName,
		SecondName: teacherReqData.SecondName,
		MiddleName: teacherReqData.MiddleName,
	}

	errCreateTeacher := s.repo.TeachersRepository.CreateTeacher(Teacher)

	if errCreateTeacher != nil {
		if errService.IsDuplicateError(errCreateTeacher) {
			return "", fmt.Errorf("failed to create teacher: teacher already exists")
		}
		return "", fmt.Errorf("failed to create teacher: %w", errCreateTeacher)
	}

	return teacherUUID, nil
}
