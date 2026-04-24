package subjectTypes

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type SubjectTypesRepository struct {
	Pool *pgxpool.Pool
}

func NewSubjectTypesRepository(pool *pgxpool.Pool) *SubjectTypesRepository {
	return &SubjectTypesRepository{
		Pool: pool,
	}
}
