package schedule

import (
	"fmt"
	"raspyx2/internal/models"
	"raspyx2/internal/service/errService"
	"strings"
)

func (s *ScheduleService) DeleteSchedule(scheduleUUID string) error {
	err := s.repo.ScheduleRepository.DeleteSchedule(scheduleUUID)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("failed to delete schedule: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("failed to delete schedule: schedule not found: %w", err)
		}
		return err
	}

	return nil
}

func (s *ScheduleService) DeleteScheduleByFilters(filters *models.DeleteScheduleFilters) error {
	err := s.repo.ScheduleRepository.DeleteScheduleByFilters(filters)

	if err != nil {
		if errService.IsForeignKeyError(err) {
			return fmt.Errorf("failed to delete schedule: it is being referenced by other records: %w", err)
		}
		if strings.Contains(err.Error(), "nonexisting row") {
			return fmt.Errorf("failed to delete schedule: schedule not found: %w", err)
		}
		return err
	}

	return nil
}
