package subjects

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectsRepository) GetAllSubjects() (*[]models.Subject, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Subjects []models.Subject

	for rows.Next() {
		var Subject models.Subject

		errScan := rows.Scan(
			&Subject.UUID,
			&Subject.Name,
		)

		if errScan != nil {
			return nil, errScan
		}

		Subjects = append(Subjects, Subject)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Subjects, nil
}

func (r *SubjectsRepository) GetSubjectsByName(subjectName string) (*[]models.Subject, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(name) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+subjectName+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var Subjects []models.Subject

	for rows.Next() {
		var Subject models.Subject

		errScan := rows.Scan(
			&Subject.UUID,
			&Subject.Name,
		)

		if errScan != nil {
			return nil, errScan
		}

		Subjects = append(Subjects, Subject)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &Subjects, nil
}

func (r *SubjectsRepository) GetSubjectByName(subjectName string) (*models.Subject, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(name)=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, subjectName)

	var Subject models.Subject

	errScan := row.Scan(
		&Subject.UUID,
		&Subject.Name,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Subject, nil
}

func (r *SubjectsRepository) GetSubjectByUUID(subjectUUID string) (*models.Subject, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECTS_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, subjectUUID)

	var Subject models.Subject

	errScan := row.Scan(
		&Subject.UUID,
		&Subject.Name,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Subject, nil
}
