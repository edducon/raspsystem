package schedule

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type ScheduleRepository struct {
	Pool *pgxpool.Pool
}

func NewScheduleRepository(pool *pgxpool.Pool) *ScheduleRepository {
	return &ScheduleRepository{
		Pool: pool,
	}
}
