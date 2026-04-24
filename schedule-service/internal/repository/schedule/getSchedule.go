package schedule

import (
	"context"
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/constRepository"
	"strings"
)

func (r *ScheduleRepository) GetScheduleByGroupUUID(groupUUID string, isSession bool) (*[]models.GetSchedule, error) {
	query := fmt.Sprintf(
		`SELECT
		g.uuid, g.number,
		sbj.uuid, sbj.name,
		st.uuid, st.type,
		l.uuid, l.name,
		s.start_time, s.end_time, s.start_date, s.end_date, s.weekday, COALESCE(s.link, ''), s.is_session,
		ARRAY_AGG(DISTINCT(
			CASE
				WHEN t.uuid IS NULL THEN ''
				ELSE TRIM(CONCAT(t.uuid, '|', t.second_name, ' ', t.first_name, ' ', COALESCE(t.middle_name, '')))
			END
		)),
    	ARRAY_AGG(DISTINCT
			CASE
				WHEN r.uuid IS NULL THEN ''
				ELSE CONCAT(r.uuid, '|', COALESCE(r.number, ''))
			END
		)
	FROM %s s
         LEFT JOIN %s g ON s.group_uuid = g.uuid
         LEFT JOIN %s sbj ON s.subject_uuid = sbj.uuid
         LEFT JOIN %s st ON s.subject_type_uuid = st.uuid
         LEFT JOIN %s l ON s.location_uuid = l.uuid
         LEFT JOIN %s ttos ON s.uuid = ttos.schedule_uuid
         LEFT JOIN %s t ON ttos.teacher_uuid = t.uuid
         LEFT JOIN %s rtos ON s.uuid = rtos.schedule_uuid
         LEFT JOIN %s r ON rtos.room_uuid = r.uuid
	WHERE g.uuid = $1 AND s.is_session = $2
	GROUP BY s.uuid, g.uuid, g.number, sbj.uuid, sbj.name, st.uuid, st.type, l.uuid,
		l.name, s.start_time, s.end_time, s.start_date, s.end_date, s.weekday,
        s.link, s.is_session`,
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.GROUPS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECTS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECT_TYPES_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.LOCATIONS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TABLE),
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, groupUUID, isSession)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var allSchedule []models.GetSchedule

	for rows.Next() {
		var schedule models.GetSchedule

		schedule.Group = &models.Group{}
		schedule.Subject = &models.Subject{}
		schedule.SubjectType = &models.SubjectType{}
		schedule.Location = &models.Location{}
		schedule.Teachers = &[]models.GetTeacherResponse{}
		schedule.Rooms = &[]models.Room{}

		var teachers, rooms []string

		errScan := rows.Scan(
			&schedule.Group.UUID,
			&schedule.Group.Number,
			&schedule.Subject.UUID,
			&schedule.Subject.Name,
			&schedule.SubjectType.UUID,
			&schedule.SubjectType.Type,
			&schedule.Location.UUID,
			&schedule.Location.Name,
			&schedule.StartTime,
			&schedule.EndTime,
			&schedule.StartDate,
			&schedule.EndDate,
			&schedule.Weekday,
			&schedule.Link,
			&schedule.IsSession,
			&teachers,
			&rooms,
		)

		for _, teacher := range teachers {
			splitedTeacher := strings.Split(teacher, "|")
			if len(splitedTeacher) != 2 {
				continue
			}
			*schedule.Teachers = append(*schedule.Teachers, models.GetTeacherResponse{
				UUID:     splitedTeacher[0],
				FullName: splitedTeacher[1],
			})
		}

		for _, room := range rooms {
			splitedRoom := strings.Split(room, "|")
			if len(splitedRoom) != 2 {
				continue
			}
			*schedule.Rooms = append(*schedule.Rooms, models.Room{
				UUID:   splitedRoom[0],
				Number: splitedRoom[1],
			})
		}

		if errScan != nil {
			return nil, errScan
		}

		allSchedule = append(allSchedule, schedule)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &allSchedule, nil
}

func (r *ScheduleRepository) GetScheduleByTeacherUUID(teacherUUID string, isSession bool) (*[]models.GetSchedule, error) {
	query := fmt.Sprintf(
		`SELECT
		g.uuid, g.number,
		sbj.uuid, sbj.name,
		st.uuid, st.type,
		l.uuid, l.name,
		s.start_time, s.end_time, s.start_date, s.end_date, s.weekday, COALESCE(s.link, ''), s.is_session,
		ARRAY_AGG(DISTINCT(
			CASE
				WHEN t.uuid IS NULL THEN ''
				ELSE TRIM(CONCAT(t.uuid, '|', t.second_name, ' ', t.first_name, ' ', COALESCE(t.middle_name, '')))
			END
		)),
    	ARRAY_AGG(DISTINCT
			CASE
				WHEN r.uuid IS NULL THEN ''
				ELSE CONCAT(r.uuid, '|', COALESCE(r.number, ''))
			END
		)
	FROM %s s
         LEFT JOIN %s g ON s.group_uuid = g.uuid
         LEFT JOIN %s sbj ON s.subject_uuid = sbj.uuid
         LEFT JOIN %s st ON s.subject_type_uuid = st.uuid
         LEFT JOIN %s l ON s.location_uuid = l.uuid
         LEFT JOIN %s ttos ON s.uuid = ttos.schedule_uuid
         LEFT JOIN %s t ON ttos.teacher_uuid = t.uuid
         LEFT JOIN %s rtos ON s.uuid = rtos.schedule_uuid
         LEFT JOIN %s r ON rtos.room_uuid = r.uuid
	WHERE t.uuid = $1 AND s.is_session = $2
	GROUP BY s.uuid, g.uuid, g.number, sbj.uuid, sbj.name, st.uuid, st.type, l.uuid,
		l.name, s.start_time, s.end_time, s.start_date, s.end_date, s.weekday,
        s.link, s.is_session`,
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.GROUPS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECTS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECT_TYPES_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.LOCATIONS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TABLE),
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, teacherUUID, isSession)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var allSchedule []models.GetSchedule

	for rows.Next() {
		var schedule models.GetSchedule

		schedule.Group = &models.Group{}
		schedule.Subject = &models.Subject{}
		schedule.SubjectType = &models.SubjectType{}
		schedule.Location = &models.Location{}
		schedule.Teachers = &[]models.GetTeacherResponse{}
		schedule.Rooms = &[]models.Room{}

		var teachers, rooms []string

		errScan := rows.Scan(
			&schedule.Group.UUID,
			&schedule.Group.Number,
			&schedule.Subject.UUID,
			&schedule.Subject.Name,
			&schedule.SubjectType.UUID,
			&schedule.SubjectType.Type,
			&schedule.Location.UUID,
			&schedule.Location.Name,
			&schedule.StartTime,
			&schedule.EndTime,
			&schedule.StartDate,
			&schedule.EndDate,
			&schedule.Weekday,
			&schedule.Link,
			&schedule.IsSession,
			&teachers,
			&rooms,
		)

		for _, teacher := range teachers {
			splitedTeacher := strings.Split(teacher, "|")
			if len(splitedTeacher) != 2 {
				continue
			}
			*schedule.Teachers = append(*schedule.Teachers, models.GetTeacherResponse{
				UUID:     splitedTeacher[0],
				FullName: splitedTeacher[1],
			})
		}

		for _, room := range rooms {
			splitedRoom := strings.Split(room, "|")
			if len(splitedRoom) != 2 {
				continue
			}
			*schedule.Rooms = append(*schedule.Rooms, models.Room{
				UUID:   splitedRoom[0],
				Number: splitedRoom[1],
			})
		}

		if errScan != nil {
			return nil, errScan
		}

		allSchedule = append(allSchedule, schedule)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &allSchedule, nil
}
func (r *ScheduleRepository) GetScheduleByLocationUUID(locationUUID string, isSession bool) (*[]models.GetSchedule, error) {
    query := fmt.Sprintf(
       `SELECT
       g.uuid, g.number,
       sbj.uuid, sbj.name,
       st.uuid, st.type,
       l.uuid, l.name,
       s.start_time, s.end_time, s.start_date, s.end_date, s.weekday, COALESCE(s.link, ''), s.is_session,
       ARRAY_AGG(DISTINCT(
          CASE
             WHEN t.uuid IS NULL THEN ''
             ELSE TRIM(CONCAT(t.uuid, '|', t.second_name, ' ', t.first_name, ' ', COALESCE(t.middle_name, '')))
          END
       )),
        ARRAY_AGG(DISTINCT
          CASE
             WHEN r.uuid IS NULL THEN ''
             ELSE CONCAT(r.uuid, '|', COALESCE(r.number, ''))
          END
       )
    FROM %s s
         LEFT JOIN %s g ON s.group_uuid = g.uuid
         LEFT JOIN %s sbj ON s.subject_uuid = sbj.uuid
         LEFT JOIN %s st ON s.subject_type_uuid = st.uuid
         LEFT JOIN %s l ON s.location_uuid = l.uuid
         LEFT JOIN %s ttos ON s.uuid = ttos.schedule_uuid
         LEFT JOIN %s t ON ttos.teacher_uuid = t.uuid
         LEFT JOIN %s rtos ON s.uuid = rtos.schedule_uuid
         LEFT JOIN %s r ON rtos.room_uuid = r.uuid
    WHERE l.uuid = $1 AND s.is_session = $2
    GROUP BY s.uuid, g.uuid, g.number, sbj.uuid, sbj.name, st.uuid, st.type, l.uuid,
       l.name, s.start_time, s.end_time, s.start_date, s.end_date, s.weekday,
        s.link, s.is_session`,
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SCHEDULE_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.GROUPS_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECTS_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECT_TYPES_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.LOCATIONS_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TO_SCHEDULE_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TO_SCHEDULE_TABLE),
       fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TABLE),
    )

    ctx := context.Background()
    rows, err := r.Pool.Query(ctx, query, locationUUID, isSession)
    if err != nil {
       return nil, err
    }

    defer rows.Close()

    var allSchedule []models.GetSchedule

    for rows.Next() {
       var schedule models.GetSchedule

       schedule.Group = &models.Group{}
       schedule.Subject = &models.Subject{}
       schedule.SubjectType = &models.SubjectType{}
       schedule.Location = &models.Location{}
       schedule.Teachers = &[]models.GetTeacherResponse{}
       schedule.Rooms = &[]models.Room{}

       var teachers, rooms []string

       errScan := rows.Scan(
          &schedule.Group.UUID,
          &schedule.Group.Number,
          &schedule.Subject.UUID,
          &schedule.Subject.Name,
          &schedule.SubjectType.UUID,
          &schedule.SubjectType.Type,
          &schedule.Location.UUID,
          &schedule.Location.Name,
          &schedule.StartTime,
          &schedule.EndTime,
          &schedule.StartDate,
          &schedule.EndDate,
          &schedule.Weekday,
          &schedule.Link,
          &schedule.IsSession,
          &teachers,
          &rooms,
       )

       for _, teacher := range teachers {
          splitedTeacher := strings.Split(teacher, "|")
          if len(splitedTeacher) != 2 {
             continue
          }
          *schedule.Teachers = append(*schedule.Teachers, models.GetTeacherResponse{
             UUID:     splitedTeacher[0],
             FullName: splitedTeacher[1],
          })
       }

       for _, room := range rooms {
          splitedRoom := strings.Split(room, "|")
          if len(splitedRoom) != 2 {
             continue
          }
          *schedule.Rooms = append(*schedule.Rooms, models.Room{
             UUID:   splitedRoom[0],
             Number: splitedRoom[1],
          })
       }

       if errScan != nil {
          return nil, errScan
       }

       allSchedule = append(allSchedule, schedule)
    }

    if err = rows.Err(); err != nil {
       return nil, err
    }

    return &allSchedule, nil
}
func (r *ScheduleRepository) GetAllSchedule(isSession bool) (*[]models.GetSchedule, error) {
	query := fmt.Sprintf(
		`SELECT
		g.uuid, g.number,
		sbj.uuid, sbj.name,
		st.uuid, st.type,
		l.uuid, l.name,
		s.start_time, s.end_time, s.start_date, s.end_date, s.weekday, COALESCE(s.link, ''), s.is_session,
		ARRAY_AGG(DISTINCT(
			CASE
				WHEN t.uuid IS NULL THEN ''
				ELSE TRIM(CONCAT(t.uuid, '|', t.second_name, ' ', t.first_name, ' ', COALESCE(t.middle_name, '')))
			END
		)),
    	ARRAY_AGG(DISTINCT
			CASE
				WHEN r.uuid IS NULL THEN ''
				ELSE CONCAT(r.uuid, '|', COALESCE(r.number, ''))
			END
		)
	FROM %s s
         LEFT JOIN %s g ON s.group_uuid = g.uuid
         LEFT JOIN %s sbj ON s.subject_uuid = sbj.uuid
         LEFT JOIN %s st ON s.subject_type_uuid = st.uuid
         LEFT JOIN %s l ON s.location_uuid = l.uuid
         LEFT JOIN %s ttos ON s.uuid = ttos.schedule_uuid
         LEFT JOIN %s t ON ttos.teacher_uuid = t.uuid
         LEFT JOIN %s rtos ON s.uuid = rtos.schedule_uuid
         LEFT JOIN %s r ON rtos.room_uuid = r.uuid
	WHERE s.is_session = $1
	GROUP BY s.uuid, g.uuid, g.number, sbj.uuid, sbj.name, st.uuid, st.type, l.uuid,
		l.name, s.start_time, s.end_time, s.start_date, s.end_date, s.weekday,
        s.link, s.is_session`,
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.GROUPS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECTS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.SUBJECT_TYPES_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.LOCATIONS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.TEACHERS_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TO_SCHEDULE_TABLE),
		fmt.Sprintf("%s.%s", constRepository.RASPYX_SCHEMA, constRepository.ROOMS_TABLE),
	)

	ctx := context.Background()
	rows, err := r.Pool.Query(ctx, query, isSession)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var allSchedule []models.GetSchedule

	for rows.Next() {
		var schedule models.GetSchedule

		schedule.Group = &models.Group{}
		schedule.Subject = &models.Subject{}
		schedule.SubjectType = &models.SubjectType{}
		schedule.Location = &models.Location{}
		schedule.Teachers = &[]models.GetTeacherResponse{}
		schedule.Rooms = &[]models.Room{}

		var teachers, rooms []string

		errScan := rows.Scan(
			&schedule.Group.UUID,
			&schedule.Group.Number,
			&schedule.Subject.UUID,
			&schedule.Subject.Name,
			&schedule.SubjectType.UUID,
			&schedule.SubjectType.Type,
			&schedule.Location.UUID,
			&schedule.Location.Name,
			&schedule.StartTime,
			&schedule.EndTime,
			&schedule.StartDate,
			&schedule.EndDate,
			&schedule.Weekday,
			&schedule.Link,
			&schedule.IsSession,
			&teachers,
			&rooms,
		)

		for _, teacher := range teachers {
			splitedTeacher := strings.Split(teacher, "|")
			if len(splitedTeacher) != 2 {
				continue
			}
			*schedule.Teachers = append(*schedule.Teachers, models.GetTeacherResponse{
				UUID:     splitedTeacher[0],
				FullName: splitedTeacher[1],
			})
		}

		for _, room := range rooms {
			splitedRoom := strings.Split(room, "|")
			if len(splitedRoom) != 2 {
				continue
			}
			*schedule.Rooms = append(*schedule.Rooms, models.Room{
				UUID:   splitedRoom[0],
				Number: splitedRoom[1],
			})
		}

		if errScan != nil {
			return nil, errScan
		}

		allSchedule = append(allSchedule, schedule)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return &allSchedule, nil
}