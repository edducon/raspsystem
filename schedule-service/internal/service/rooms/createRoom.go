package rooms

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *RoomsService) CreateRoom(roomReqData *models.AddRoomRequest) (string, error) {
	roomUUID := uuid.NewString()

	Room := &models.Room{
		UUID:   roomUUID,
		Number: roomReqData.Number,
	}

	errCreateRoom := s.repo.RoomsRepository.CreateRoom(Room)

	if errCreateRoom != nil {
		if errService.IsDuplicateError(errCreateRoom) {
			return "", fmt.Errorf("failed to create room: room already exists")
		}
		return "", fmt.Errorf("failed to create room: %w", errCreateRoom)
	}

	return roomUUID, nil
}
