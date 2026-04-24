package locations

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *LocationsService) UpdateLocation(locationUUID string, locationData *models.UpdateLocationRequest) error {
	errUpdateLocation := s.repo.LocationsRepository.UpdateLocation(locationUUID, locationData)

	if errUpdateLocation != nil {
		if errService.IsDuplicateError(errUpdateLocation) {
			return fmt.Errorf("failed to update location: target location already exists")
		}
		return fmt.Errorf("failed to update location: %w", errUpdateLocation)
	}

	return nil
}
