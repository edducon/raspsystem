package locations

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *LocationsRepository) CreateLocation(locationData *models.Location) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"name) "+
		"VALUES ($1, $2)",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE),
		locationData.UUID,
		locationData.Name,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
