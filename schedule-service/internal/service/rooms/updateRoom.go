package rooms

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *RoomsService) UpdateRoom(roomUUID string, roomData *models.UpdateRoomRequest) error {
	errUpdateRoom := s.repo.RoomsRepository.UpdateRoom(roomUUID, roomData)

	if errUpdateRoom != nil {
		if errService.IsDuplicateError(errUpdateRoom) {
			return fmt.Errorf("failed to update room: target room already exists")
		}
		return fmt.Errorf("failed to update room: %w", errUpdateRoom)
	}

	return nil
}
