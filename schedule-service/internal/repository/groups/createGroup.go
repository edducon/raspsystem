package groups

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *GroupsRepository) CreateGroup(groupData *models.Group) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"number) "+
		"VALUES ($1, $2)",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE),
		groupData.UUID,
		groupData.Number,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
