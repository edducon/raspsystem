package subjectTypes

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *SubjectTypesRepository) GetAllSubjectTypes() (*[]models.SubjectType, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var SubjectTypes []models.SubjectType

	for rows.Next() {
		var Subject models.SubjectType

		errScan := rows.Scan(
			&Subject.UUID,
			&Subject.Type,
		)

		if errScan != nil {
			return nil, errScan
		}

		SubjectTypes = append(SubjectTypes, Subject)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &SubjectTypes, nil
}

func (r *SubjectTypesRepository) GetSubjectTypesByType(subjectType string) (*[]models.SubjectType, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(type) LIKE LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE,
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, "%"+subjectType+"%")
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var SubjectTypes []models.SubjectType

	for rows.Next() {
		var Subject models.SubjectType

		errScan := rows.Scan(
			&Subject.UUID,
			&Subject.Type,
		)

		if errScan != nil {
			return nil, errScan
		}

		SubjectTypes = append(SubjectTypes, Subject)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &SubjectTypes, nil
}

func (r *SubjectTypesRepository) GetSubjectTypeByType(subjectType string) (*models.SubjectType, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE LOWER(type)=LOWER($1)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, subjectType)

	var Subject models.SubjectType

	errScan := row.Scan(
		&Subject.UUID,
		&Subject.Type,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Subject, nil
}

func (r *SubjectTypesRepository) GetSubjectTypeByUUID(subjectTypeUUID string) (*models.SubjectType, error) {
	query := fmt.Sprintf("SELECT * FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.SUBJECT_TYPES_TABLE,
	)

	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query, subjectTypeUUID)

	var Subject models.SubjectType

	errScan := row.Scan(
		&Subject.UUID,
		&Subject.Type,
	)

	if errScan != nil {
		return nil, errScan
	}

	return &Subject, nil
}
