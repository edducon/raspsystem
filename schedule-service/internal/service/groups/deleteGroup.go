package groups

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *GroupsService) DeleteGroup(groupUUID string) error {
	err := s.repo.GroupsRepository.DeleteGroup(groupUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete group: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("group not found: %w", err)
		}
		return err
	}

	return nil
}
