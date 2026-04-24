package groups

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *GroupsService) GetAllGroups() (*[]models.Group, error) {
	return s.repo.GroupsRepository.GetAllGroups()
}

func (s *GroupsService) GetGroupsByNumber(groupNumber string) (*[]models.Group, error) {
	return s.repo.GroupsRepository.GetGroupsByNumber(groupNumber)
}

func (s *GroupsService) GetGroupByNumber(groupNumber string) (*models.Group, error) {
	groups, err := s.repo.GroupsRepository.GetGroupsByNumber(groupNumber)
	if err != nil {
		return nil, fmt.Errorf("error get group by number: %s", groupNumber)
	}

	var group *models.Group
	for _, g := range *groups {
		if g.Number == groupNumber {
			group = &g
			break
		}
	}

	if group == nil {
		return nil, fmt.Errorf("error get group by number: %s", groupNumber)
	}

	return group, nil
}

func (s *GroupsService) GetGroupByUUID(groupUUID string) (*models.Group, error) {
	return s.repo.GroupsRepository.GetGroupByUUID(groupUUID)
}
