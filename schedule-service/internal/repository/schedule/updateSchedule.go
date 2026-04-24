package schedule

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *ScheduleRepository) UpdateSchedule(scheduleUUID string, scheduleData *models.UpdateScheduleRequest) error {
	query := fmt.Sprintf("UPDATE %s.%s SET "+
		"group_uuid=$1, "+
		"subject_uuid=$2, "+
		"subject_type_uuid=$3, "+
		"location_uuid=$4, "+
		"start_time=$5, "+
		"end_time=$6, "+
		"start_date=$7, "+
		"end_date=$8, "+
		"weekday=$9, "+
		"link=$10, "+
		"is_session=$11 "+
		"WHERE uuid=$12 "+
		"RETURNING uuid",
		constRepository.RASPYX_SCHEMA,
		constRepository.SCHEDULE_TABLE)

	var updatedUUID string
	ctx := context.Background()
	row := r.Pool.QueryRow(ctx, query,
		scheduleData.GroupUUID,
		scheduleData.SubjectUUID,
		scheduleData.SubjectTypeUUID,
		scheduleData.LocationUUID,
		scheduleData.StartTime,
		scheduleData.EndTime,
		scheduleData.StartDate,
		scheduleData.EndDate,
		scheduleData.Weekday,
		scheduleData.Link,
		scheduleData.IsSession,
		scheduleUUID,
	)

	errUpdate := row.Scan(&updatedUUID)

	if errUpdate != nil {
		return errUpdate
	}

	return nil
}
