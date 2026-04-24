package schedule

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
)

func (r *ScheduleRepository) CreateSchedule(scheduleData *models.CreateSchedule) error {
	ctx := context.Background()
	tx, err := r.Pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	_, errInsert := tx.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
		"uuid, "+
		"group_uuid, "+
		"subject_uuid, "+
		"subject_type_uuid, "+
		"location_uuid, "+
		"start_time, "+
		"end_time, "+
		"start_date, "+
		"end_date, "+
		"weekday, "+
		"link, "+
		"is_session) "+
		"VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
		constRepository.RASPYX_SCHEMA,
		constRepository.SCHEDULE_TABLE),
		scheduleData.UUID,
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
	)
	if errInsert != nil {
		return errInsert
	}

	for _, t := range scheduleData.TeachersUUID {
		_, errInsert = tx.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
			"teacher_uuid, "+
			"schedule_uuid) "+
			"VALUES ($1, $2)",
			constRepository.RASPYX_SCHEMA,
			constRepository.TEACHERS_TO_SCHEDULE_TABLE),
			t.TeacherUUID,
			scheduleData.UUID,
		)

		if errInsert != nil {
			return errInsert
		}
	}

	for _, r := range scheduleData.RoomsUUID {
		_, errInsert = tx.Exec(ctx, fmt.Sprintf("INSERT INTO %s.%s ("+
			"room_uuid, "+
			"schedule_uuid) "+
			"VALUES ($1, $2)",
			constRepository.RASPYX_SCHEMA,
			constRepository.ROOMS_TO_SCHEDULE_TABLE),
			r.RoomUUID,
			scheduleData.UUID,
		)

		if errInsert != nil {
			return errInsert
		}
	}

	return tx.Commit(ctx)
}
