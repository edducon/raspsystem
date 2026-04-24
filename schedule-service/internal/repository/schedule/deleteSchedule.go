package schedule

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *ScheduleRepository) DeleteSchedule(scheduleUUID string) error {
	ctx := context.Background()
	dataDelete, errDelete := r.Pool.Exec(ctx, fmt.Sprintf("DELETE FROM %s.%s WHERE uuid=$1",
		constRepository.RASPYX_SCHEMA,
		constRepository.SCHEDULE_TABLE),
		scheduleUUID,
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

func (r *ScheduleRepository) DeleteScheduleByFilters(filters *models.DeleteScheduleFilters) error {
	query, args := makeQuery(filters)
	dataDelete, errDelete := r.Pool.Exec(context.Background(), query, *args...)
	if errDelete != nil {
		return errDelete
	}

	rowsAffected := dataDelete.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("nonexisting row")
	}

	return nil
}

func makeQuery(filters *models.DeleteScheduleFilters) (string, *[]interface{}) {
	query := fmt.Sprintf("DELETE FROM %s.%s WHERE",
		constRepository.RASPYX_SCHEMA, constRepository.SCHEDULE_TABLE,
	)

	argIndex := 1
	var args []interface{}
	if filters.GroupUUID != "" {
		query += fmt.Sprintf(" group_uuid = $%d", argIndex)
		args = append(args, filters.GroupUUID)
		argIndex++
	} else {
		query += fmt.Sprintf(" group_uuid = $%d", argIndex)
		args = append(args, "null")
		return query, &args
	}

	if filters.StartTime != "" {
		query += fmt.Sprintf(" AND start_time = $%d", argIndex)
		args = append(args, filters.StartTime)
		argIndex++
	}

	if filters.EndTime != "" {
		query += fmt.Sprintf(" AND end_time = $%d", argIndex)
		args = append(args, filters.EndTime)
		argIndex++
	}

	if filters.StartDate != "" {
		query += fmt.Sprintf(" AND start_date = $%d", argIndex)
		args = append(args, filters.StartDate)
		argIndex++
	}

	if filters.EndDate != "" {
		query += fmt.Sprintf(" AND end_date = $%d", argIndex)
		args = append(args, filters.EndDate)
		argIndex++
	}

	if filters.SubjectUUID != "" {
		query += fmt.Sprintf(" AND subject_uuid = $%d", argIndex)
		args = append(args, filters.SubjectUUID)
		argIndex++
	}

	if filters.Weekday != nil {
		query += fmt.Sprintf(" AND weekday = $%d", argIndex)
		args = append(args, filters.Weekday)
		argIndex++
	}

	if filters.IsSession != nil {
		query += fmt.Sprintf(" AND is_session = $%d", argIndex)
		args = append(args, filters.IsSession)
		argIndex++
	}

	return query, &args
}
