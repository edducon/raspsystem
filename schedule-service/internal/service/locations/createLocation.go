package locations

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
)

func (s *LocationsService) CreateLocation(locationReqData *models.AddLocationRequest) (string, error) {
	locationUUID := uuid.NewString()

	Location := &models.Location{
		UUID: locationUUID,
		Name: locationReqData.Name,
	}

	errCreateLocation := s.repo.LocationsRepository.CreateLocation(Location)

	if errCreateLocation != nil {
		if errService.IsDuplicateError(errCreateLocation) {
			return "", fmt.Errorf("failed to create location: location already exists")
		}
		return "", fmt.Errorf("failed to create location: %w", errCreateLocation)
	}

	return locationUUID, nil
}
