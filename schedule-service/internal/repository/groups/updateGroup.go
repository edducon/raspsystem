package groups

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *GroupsRepository) UpdateGroup(groupUUID string, groupData *models.UpdateGroupRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"number=$1 "+
		"WHERE uuid=$2 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		groupData.Number,
		groupUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
