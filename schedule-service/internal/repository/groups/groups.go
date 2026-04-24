package groups

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type GroupsRepository struct {
	Pool *pgxpool.Pool
}

func NewGroupsRepository(pool *pgxpool.Pool) *GroupsRepository {
	return &GroupsRepository{
		Pool: pool,
	}
}
