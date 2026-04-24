package locations

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *LocationsService) GetAllLocations() (*[]models.Location, error) {
	return s.repo.LocationsRepository.GetAllLocations()
}

func (s *LocationsService) GetLocationsByName(locationName string) (*[]models.Location, error) {
	return s.repo.LocationsRepository.GetLocationsByName(locationName)
}

func (s *LocationsService) GetLocationByName(locationName string) (*models.Location, error) {
	locations, err := s.repo.LocationsRepository.GetLocationsByName(locationName)
	if err != nil {
		return nil, fmt.Errorf("error get location by name: %s", locationName)
	}

	var location *models.Location
	for _, l := range *locations {
		if l.Name == locationName {
			location = &l
			break
		}
	}

	if location == nil {
		return nil, fmt.Errorf("error get location by name: %s", locationName)
	}

	return location, nil
}

func (s *LocationsService) GetLocationByUUID(locationUUID string) (*models.Location, error) {
	return s.repo.LocationsRepository.GetLocationByUUID(locationUUID)
}
