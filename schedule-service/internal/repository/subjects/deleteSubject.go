package subjects

import (
	"context"
	"fmt"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectsRepository) DeleteSubject(subjectUUID string) error {
	ctx := context.Background()
	dataDelete, errDelete := r.Pool.Exec(ctx, fmt.Sprintf("DELETE FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE),
		subjectUUID,
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
