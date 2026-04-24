package locations

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type LocationsRepository struct {
	Pool *pgxpool.Pool
}

func NewLocationsRepository(pool *pgxpool.Pool) *LocationsRepository {
	return &LocationsRepository{
		Pool: pool,
	}
}
