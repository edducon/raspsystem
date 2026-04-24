package subjects

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectsRepository) UpdateSubject(subjectUUID string, subjectData *models.UpdateSubjectRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"name=$1 "+
		"WHERE uuid=$2 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		subjectData.Name,
		subjectUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
