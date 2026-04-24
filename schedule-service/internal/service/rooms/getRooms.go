package rooms

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *RoomsService) GetAllRooms() (*[]models.Room, error) {
	return s.repo.RoomsRepository.GetAllRooms()
}

func (s *RoomsService) GetRoomsByNumber(roomNumber string) (*[]models.Room, error) {
	return s.repo.RoomsRepository.GetRoomsByNumber(roomNumber)
}

func (s *RoomsService) GetRoomByNumber(roomNumber string) (*models.Room, error) {
	rooms, err := s.repo.RoomsRepository.GetRoomsByNumber(roomNumber)
	if err != nil {
		return nil, fmt.Errorf("error get room by number: %s", roomNumber)
	}

	var room *models.Room
	for _, r := range *rooms {
		if r.Number == roomNumber {
			room = &r
			break
		}
	}

	if room == nil {
		return nil, fmt.Errorf("error get room by number: %s", roomNumber)
	}

	return room, nil
}

func (s *RoomsService) GetRoomByUUID(roomUUID string) (*models.Room, error) {
	return s.repo.RoomsRepository.GetRoomByUUID(roomUUID)
}
