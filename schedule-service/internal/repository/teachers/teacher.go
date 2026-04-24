package teachers

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type TeachersRepository struct {
	Pool *pgxpool.Pool
}

func NewTeachersRepository(pool *pgxpool.Pool) *TeachersRepository {
	return &TeachersRepository{
		Pool: pool,
	}
}
