package teachers

import (
	"fmt"
	"raspyx2/internal/models"
	"strings"
)

func (s *TeachersService) GetAllTeachers() (*[]models.GetTeacherResponse, error) {
	teachers, err := s.repo.TeachersRepository.GetAllTeachers()
	if err != nil {
		return nil, err
	}

	var teachersResponse []models.GetTeacherResponse
	for _, teacher := range *teachers {
		teachersResponse = append(teachersResponse, models.GetTeacherResponse{
			UUID: teacher.UUID,
			FullName: strings.TrimSpace(fmt.Sprintf("%s %s %s",
				teacher.SecondName,
				teacher.FirstName,
				teacher.MiddleName,
			)),
		})
	}

	return &teachersResponse, nil
}

func (s *TeachersService) GetTeachersByFio(teacherFio string) (*[]models.GetTeacherResponse, error) {
	teachers, err := s.repo.TeachersRepository.GetTeachersByFio(teacherFio)
	if err != nil {
		return nil, err
	}

	var teachersResponse []models.GetTeacherResponse
	for _, teacher := range *teachers {
		teachersResponse = append(teachersResponse, models.GetTeacherResponse{
			UUID: teacher.UUID,
			FullName: strings.TrimSpace(fmt.Sprintf("%s %s %s",
				teacher.SecondName,
				teacher.FirstName,
				teacher.MiddleName,
			)),
		})
	}

	return &teachersResponse, nil
}

func (s *TeachersService) GetTeacherByFio(teacherFio string) (*models.Teacher, error) {
	teachers, err := s.repo.TeachersRepository.GetTeachersByFio(teacherFio)
	if err != nil {
		return nil, fmt.Errorf("error get teacher by fio: %s", teacherFio)
	}

	var teacher *models.Teacher
	for _, t := range *teachers {
		if strings.TrimSpace(fmt.Sprintf("%s %s %s", t.SecondName, t.FirstName, t.MiddleName)) == teacherFio {
			teacher = &t
			break
		}
	}

	if teacher == nil {
		return nil, fmt.Errorf("error get teacher by fio: %s", teacherFio)
	}

	return teacher, nil
}

func (s *TeachersService) GetTeacherByUUID(teacherUUID string) (*models.GetTeacherResponse, error) {
	teacher, err := s.repo.TeachersRepository.GetTeacherByUUID(teacherUUID)
	if err != nil {
		return nil, err
	}

	return &models.GetTeacherResponse{
		UUID: teacher.UUID,
		FullName: strings.TrimSpace(fmt.Sprintf("%s %s %s",
			teacher.SecondName,
			teacher.FirstName,
			teacher.MiddleName,
		)),
	}, nil
}
