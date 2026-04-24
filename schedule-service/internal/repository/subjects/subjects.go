package subjects

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type SubjectsRepository struct {
	Pool *pgxpool.Pool
}

func NewSubjectsRepository(pool *pgxpool.Pool) *SubjectsRepository {
	return &SubjectsRepository{
		Pool: pool,
	}
}
