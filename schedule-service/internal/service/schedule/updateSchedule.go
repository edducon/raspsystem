package schedule

import (
	"fmt"
	"raspyx2/internal/models"
)

func (s *ScheduleService) UpdateSchedule(scheduleUUID string, scheduleData *models.UpdateScheduleRequest) error {
	errUpdateSchedule := s.repo.ScheduleRepository.UpdateSchedule(scheduleUUID, scheduleData)

	if errUpdateSchedule != nil {
		return fmt.Errorf("failed to update schedule: %w", errUpdateSchedule)
	}

	return nil
}
