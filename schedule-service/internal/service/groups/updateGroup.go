package groups

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *GroupsService) UpdateGroup(groupUUID string, groupData *models.UpdateGroupRequest) error {
	errUpdateGroup := s.repo.GroupsRepository.UpdateGroup(groupUUID, groupData)

	if errUpdateGroup != nil {
		if errService.IsDuplicateError(errUpdateGroup) {
			return fmt.Errorf("failed to update group: target group already exists")
		}
		return fmt.Errorf("failed to update group: %w", errUpdateGroup)
	}

	return nil
}
