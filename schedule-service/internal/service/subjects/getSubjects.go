package subjects

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *SubjectsService) GetAllSubjects() (*[]models.Subject, error) {
	return s.repo.SubjectsRepository.GetAllSubjects()
}

func (s *SubjectsService) GetSubjectsByName(subjectName string) (*[]models.Subject, error) {
	return s.repo.SubjectsRepository.GetSubjectsByName(subjectName)
}

func (s *SubjectsService) GetSubjectByName(subjectName string) (*models.Subject, error) {
	subjects, err := s.repo.SubjectsRepository.GetSubjectsByName(subjectName)
	if err != nil {
		return nil, fmt.Errorf("error get subject by name: %s", subjectName)
	}

	var subject *models.Subject
	for _, sbj := range *subjects {
		if sbj.Name == subjectName {
			subject = &sbj
			break
		}
	}

	if subject == nil {
		return nil, fmt.Errorf("error get subject by name: %s", subjectName)
	}

	return subject, nil
}

func (s *SubjectsService) GetSubjectByUUID(subjectUUID string) (*models.Subject, error) {
	return s.repo.SubjectsRepository.GetSubjectByUUID(subjectUUID)
}
