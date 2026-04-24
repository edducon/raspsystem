package rooms

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *RoomsService) DeleteRoom(roomUUID string) error {
	err := s.repo.RoomsRepository.DeleteRoom(roomUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete room: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("room not found: %w", err)
		}
		return err
	}

	return nil
}
