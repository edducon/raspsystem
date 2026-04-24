package locations

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *LocationsRepository) UpdateLocation(locationUUID string, locationData *models.UpdateLocationRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"name=$1 "+
		"WHERE uuid=$2 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		locationData.Name,
		locationUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
