package rooms

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *RoomsRepository) GetAllRooms() (*[]models.Room, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Rooms []models.Room

	for rows.Next() {
		var Room models.Room

		errScan := rows.Scan(
			&Room.UUID,
			&Room.Number,
		)

		if errScan != nil {
			return nil, errScan
		}

		Rooms = append(Rooms, Room)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Rooms, nil
}

func (r *RoomsRepository) GetRoomsByNumber(roomNumber string) (*[]models.Room, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(number) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+roomNumber+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Rooms []models.Room

	for rows.Next() {
		var Room models.Room

		errScan := rows.Scan(
			&Room.UUID,
			&Room.Number,
		)

		if errScan != nil {
			return nil, errScan
		}

		Rooms = append(Rooms, Room)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Rooms, nil
}

func (r *RoomsRepository) GetRoomByNumber(roomNumber string) (*models.Room, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(number)=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, roomNumber)

	var Room models.Room

	errScan := row.Scan(
		&Room.UUID,
		&Room.Number,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Room, nil
}

func (r *RoomsRepository) GetRoomByUUID(roomUUID string) (*models.Room, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, roomUUID)

	var Room models.Room

	errScan := row.Scan(
		&Room.UUID,
		&Room.Number,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Room, nil
}
