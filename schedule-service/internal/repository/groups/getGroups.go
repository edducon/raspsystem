package groups

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *GroupsRepository) GetAllGroups() (*[]models.Group, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Groups []models.Group

	for rows.Next() {
		var Group models.Group

		errScan := rows.Scan(
			&Group.UUID,
			&Group.Number,
		)

		if errScan != nil {
			return nil, errScan
		}

		Groups = append(Groups, Group)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Groups, nil
}

func (r *GroupsRepository) GetGroupsByNumber(groupNumber string) (*[]models.Group, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(number) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+groupNumber+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Groups []models.Group

	for rows.Next() {
		var Group models.Group

		errScan := rows.Scan(
			&Group.UUID,
			&Group.Number,
		)

		if errScan != nil {
			return nil, errScan
		}

		Groups = append(Groups, Group)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Groups, nil
}

func (r *GroupsRepository) GetGroupByNumber(groupNumber string) (*models.Group, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(number)=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, groupNumber)

	var Group models.Group

	errScan := row.Scan(
		&Group.UUID,
		&Group.Number,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Group, nil
}

func (r *GroupsRepository) GetGroupByUUID(groupUUID string) (*models.Group, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.GROUPS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, groupUUID)

	var Group models.Group

	errScan := row.Scan(
		&Group.UUID,
		&Group.Number,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Group, nil
}
