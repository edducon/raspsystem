package teachers

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *TeachersRepository) UpdateTeacher(teacherUUID string, teacherData *models.UpdateTeacherRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"first_name=$1, "+
		"second_name=$2, "+
		"middle_name=$3 "+
		"WHERE uuid=$4 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		teacherData.FirstName,
		teacherData.SecondName,
		teacherData.MiddleName,
		teacherUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
