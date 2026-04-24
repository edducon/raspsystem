package subjectTypes

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *SubjectTypesService) GetAllSubjectTypes() (*[]models.SubjectType, error) {
	return s.repo.SubjectTypesRepository.GetAllSubjectTypes()
}

func (s *SubjectTypesService) GetSubjectTypesByType(subjectType string) (*[]models.SubjectType, error) {
	return s.repo.SubjectTypesRepository.GetSubjectTypesByType(subjectType)
}

func (s *SubjectTypesService) GetSubjectTypeByType(subjectType string) (*models.SubjectType, error) {
	subjectTypes, err := s.repo.SubjectTypesRepository.GetSubjectTypesByType(subjectType)
	if err != nil {
		return nil, fmt.Errorf("error get subject type by type: %s", subjectType)
	}

	var sbjType *models.SubjectType
	for _, st := range *subjectTypes {
		if st.Type == subjectType {
			sbjType = &st
			break
		}
	}

	if sbjType == nil {
		return nil, fmt.Errorf("error get subject type by type: %s", subjectType)
	}

	return sbjType, nil
}

func (s *SubjectTypesService) GetSubjectTypeByUUID(subjectTypeUUID string) (*models.SubjectType, error) {
	return s.repo.SubjectTypesRepository.GetSubjectTypeByUUID(subjectTypeUUID)
}
