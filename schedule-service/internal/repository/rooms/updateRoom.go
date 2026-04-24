package rooms

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *RoomsRepository) UpdateRoom(roomUUID string, roomData *models.UpdateRoomRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"number=$1 "+
		"WHERE uuid=$2 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.ROOMS_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		roomData.Number,
		roomUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
