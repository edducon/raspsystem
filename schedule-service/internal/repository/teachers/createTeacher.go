package teachers

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *TeachersRepository) CreateTeacher(teacherData *models.Teacher) error {
	ctx := context.Background()
	_, errInsert := r.Pool.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"first_name,"+
		"second_name,"+
		"middle_name) "+
		"VALUES ($1, $2, $3, $4)",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE),
		teacherData.UUID,
		teacherData.FirstName,
		teacherData.SecondName,
		teacherData.MiddleName,
	)

	if errInsert != nil {
		return errInsert
	}

	return nil
}
