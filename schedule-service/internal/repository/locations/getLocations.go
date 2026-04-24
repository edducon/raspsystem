package locations

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *LocationsRepository) GetAllLocations() (*[]models.Location, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Locations []models.Location

	for rows.Next() {
		var Location models.Location

		errScan := rows.Scan(
			&Location.UUID,
			&Location.Name,
		)

		if errScan != nil {
			return nil, errScan
		}

		Locations = append(Locations, Location)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Locations, nil
}

func (r *LocationsRepository) GetLocationsByName(locationName string) (*[]models.Location, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(name) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+locationName+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Locations []models.Location

	for rows.Next() {
		var Location models.Location

		errScan := rows.Scan(
			&Location.UUID,
			&Location.Name,
		)

		if errScan != nil {
			return nil, errScan
		}

		Locations = append(Locations, Location)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Locations, nil
}

func (r *LocationsRepository) GetLocationByName(locationName string) (*models.Location, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(name)=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, locationName)

	var Location models.Location

	errScan := row.Scan(
		&Location.UUID,
		&Location.Name,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Location, nil
}

func (r *LocationsRepository) GetLocationByUUID(locationUUID string) (*models.Location, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.LOCATIONS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, locationUUID)

	var Location models.Location

	errScan := row.Scan(
		&Location.UUID,
		&Location.Name,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Location, nil
}
