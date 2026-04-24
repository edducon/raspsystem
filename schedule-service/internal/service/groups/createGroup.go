package groups

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *GroupsService) CreateGroup(groupReqData *models.AddGroupRequest) (string, error) {
	groupUUID := uuid.NewString()

	Group := &models.Group{
		UUID:   groupUUID,
		Number: groupReqData.Number,
	}

	errCreateGroup := s.repo.GroupsRepository.CreateGroup(Group)

	if errCreateGroup != nil {
		if errService.IsDuplicateError(errCreateGroup) {
			return "", fmt.Errorf("failed to create group: group already exists")
		}
		return "", fmt.Errorf("failed to create group: %w", errCreateGroup)
	}

	return groupUUID, nil
}
