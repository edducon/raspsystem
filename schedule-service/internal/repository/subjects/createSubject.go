package subjects

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectsRepository) CreateSubject(subjectData *models.Subject) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"name) "+
		"VALUES ($1, $2)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE),
		subjectData.UUID,
		subjectData.Name,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
