package subjectTypes

import (
	"context"
	"fmt"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectTypesRepository) DeleteSubjectType(subjectTypeUUID string) error {
	ctx := context.Background()
	dataDelete, errDelete := r.Pool.Exec(ctx, fmt.Sprintf("DELETE FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE),
		subjectTypeUUID,
	)

	if errDelete != nil {
		return errDelete
	}

	rowsAffected := dataDelete.RowsAffected()

	if rowsAffected == 0 {
		return fmt.Errorf("nonexisting row")
	}

	return nil
}
