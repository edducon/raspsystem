package locations

import (
	"fmt"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *LocationsService) DeleteLocation(locationUUID string) error {
	err := s.repo.LocationsRepository.DeleteLocation(locationUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("cannot delete location: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("location not found: %w", err)
		}
		return err
	}

	return nil
}
