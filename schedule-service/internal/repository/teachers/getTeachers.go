package teachers

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *TeachersRepository) GetAllTeachers() (*[]models.Teacher, error) {
	query := fmt.Sprintf("SELECT "+
		"t.uuid,"+
		"t.first_name,"+
		"t.second_name,"+
		"COALESCE(t.middle_name, '') "+
		"FROM %s.%s t",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Teachers []models.Teacher

	for rows.Next() {
		var Teacher models.Teacher

		errScan := rows.Scan(
			&Teacher.UUID,
			&Teacher.FirstName,
			&Teacher.SecondName,
			&Teacher.MiddleName,
		)

		if errScan != nil {
			return nil, errScan
		}

		Teachers = append(Teachers, Teacher)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Teachers, nil
}

func (r *TeachersRepository) GetTeachersByFio(teacherFio string) (*[]models.Teacher, error) {
	query := fmt.Sprintf("SELECT "+
		"t.uuid,"+
		"t.first_name,"+
		"t.second_name,"+
		"COALESCE(t.middle_name, '') "+
		"FROM %s.%s t "+
		"WHERE LOWER(TRIM(CONCAT(second_name, ' ', first_name, ' ', middle_name))) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+teacherFio+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Teachers []models.Teacher

	for rows.Next() {
		var Teacher models.Teacher

		errScan := rows.Scan(
			&Teacher.UUID,
			&Teacher.FirstName,
			&Teacher.SecondName,
			&Teacher.MiddleName,
		)

		if errScan != nil {
			return nil, errScan
		}

		Teachers = append(Teachers, Teacher)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Teachers, nil
}

func (r *TeachersRepository) GetTeacherByFio(teacherFio string) (*models.Teacher, error) {
	query := fmt.Sprintf("SELECT "+
		"t.uuid,"+
		"t.first_name,"+
		"t.second_name,"+
		"COALESCE(t.middle_name, '') "+
		"FROM %s.%s t "+
		"WHERE LOWER(TRIM(CONCAT(second_name, ' ', first_name, ' ', middle_name)))=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, teacherFio)

	var Teacher models.Teacher

	errScan := row.Scan(
		&Teacher.UUID,
		&Teacher.FirstName,
		&Teacher.SecondName,
		&Teacher.MiddleName,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Teacher, nil
}

func (r *TeachersRepository) GetTeacherByUUID(teacherUUID string) (*models.Teacher, error) {
	query := fmt.Sprintf("SELECT "+
		"t.uuid,"+
		"t.first_name,"+
		"t.second_name,"+
		"COALESCE(t.middle_name, '') "+
		"FROM %s.%s t "+
		"WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.TEACHERS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, teacherUUID)

	var Teacher models.Teacher

	errScan := row.Scan(
		&Teacher.UUID,
		&Teacher.FirstName,
		&Teacher.SecondName,
		&Teacher.MiddleName,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Teacher, nil
}
