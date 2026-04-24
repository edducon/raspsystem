package rooms

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type RoomsRepository struct {
	Pool *pgxpool.Pool
}

func NewRoomsRepository(pool *pgxpool.Pool) *RoomsRepository {
	return &RoomsRepository{
		Pool: pool,
	}
}
