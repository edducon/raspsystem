package subjectTypes

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectTypesRepository) UpdateSubjectType(subjectTypeUUID string, subjectTypeData *models.UpdateSubjectTypeRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"type=$1 "+
		"WHERE uuid=$2 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		subjectTypeData.Type,
		subjectTypeUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
