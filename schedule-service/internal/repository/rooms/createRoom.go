package rooms

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *RoomsRepository) CreateRoom(roomData *models.Room) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"number) "+
		"VALUES ($1, $2)",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE),
		roomData.UUID,
		roomData.Number,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
