package subjectTypes

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectTypesRepository) CreateSubjectType(subjectTypeData *models.SubjectType) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"type) "+
		"VALUES ($1, $2)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE),
		subjectTypeData.UUID,
		subjectTypeData.Type,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
