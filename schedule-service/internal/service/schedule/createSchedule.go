package schedule

import (
	"fmt"
	"github.com/google/uuid"
	"raspyx2/internal/models"
)

func (s *ScheduleService) CreateSchedule(scheduleReqData *models.AddScheduleRequest) (string, error) {
	scheduleUUID := uuid.NewString()

	Schedule := &models.CreateSchedule{
		UUID:            scheduleUUID,
		GroupUUID:       scheduleReqData.GroupUUID,
		SubjectUUID:     scheduleReqData.SubjectUUID,
		SubjectTypeUUID: scheduleReqData.SubjectTypeUUID,
		LocationUUID:    scheduleReqData.LocationUUID,
		TeachersUUID:    scheduleReqData.TeachersUUID,
		RoomsUUID:       scheduleReqData.RoomsUUID,
		StartTime:       scheduleReqData.StartTime,
		EndTime:         scheduleReqData.EndTime,
		StartDate:       scheduleReqData.StartDate,
		EndDate:         scheduleReqData.EndDate,
		Weekday:         scheduleReqData.Weekday,
		Link:            scheduleReqData.Link,
		IsSession:       scheduleReqData.IsSession,
	}

	err := s.repo.ScheduleRepository.CreateSchedule(Schedule)

	if err != nil {
		return "", fmt.Errorf("failed to create schedule: %w", err)
	}

	return scheduleUUID, nil
}
