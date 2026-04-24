package schedule

import (
	"fmt"
	"raspyx2/internal/models"
	"strings"
)

func (s *ScheduleService) GetScheduleByGroupNumber(groupNumber string, isSession bool) (*models.Week, error) {
	groupNumber = strings.TrimSpace(groupNumber)
	groups, err := s.repo.GroupsRepository.GetGroupsByNumber(groupNumber)
	if err != nil {
		return nil, fmt.Errorf("error get group %q: %w", groupNumber, err)
	}

	var groupUUID string
	for _, group := range *groups {
		if group.Number == groupNumber {
			groupUUID = group.UUID
			break
		}
	}

	if groupUUID == "" {
		return nil, fmt.Errorf("group %q not found", groupNumber)
	}

	allSchedule, err := s.repo.ScheduleRepository.GetScheduleByGroupUUID(groupUUID, isSession)
	if err != nil {
		return nil, fmt.Errorf("error get schedule: %w", err)
	}

	return makeWeek(allSchedule), nil
}

func (s *ScheduleService) GetScheduleByTeacherFio(teacherFio string, isSession bool) (*models.Week, error) {
	teacherFio = strings.TrimSpace(teacherFio)
	teachers, err := s.repo.TeachersRepository.GetTeachersByFio(teacherFio)
	if err != nil {
		return nil, fmt.Errorf("error get teacher %q: %w", teacherFio, err)
	}

	teacherSplited := strings.Split(teacherFio, " ")
	for i := range teacherSplited {
		if len(teacherSplited[i]) == 0 {
			teacherSplited = append(teacherSplited[:i], teacherSplited[i+1:]...)
		}
	}

	var teacherUUID string
	for _, t := range *teachers {
		if strings.TrimSpace(fmt.Sprintf("%s %s %s", t.SecondName, t.FirstName, t.MiddleName)) == strings.Join(teacherSplited, " ") {
			teacherUUID = t.UUID
			break
		}
	}

	if teacherUUID == "" {
		return nil, fmt.Errorf("teacher %q not found", teacherFio)
	}

	allSchedule, err := s.repo.ScheduleRepository.GetScheduleByTeacherUUID(teacherUUID, isSession)
	if err != nil {
		return nil, fmt.Errorf("error get schedule: %w", err)
	}

	return makeWeek(allSchedule), nil
}

func (s *ScheduleService) GetScheduleByLocationName(locationName string, isSession bool) (*models.Week, error) {
    locationName = strings.TrimSpace(locationName)

    // 1. Ищем локацию по названию (используем репозиторий локаций)
    locations, err := s.repo.LocationsRepository.GetLocationsByName(locationName)
    if err != nil {
       return nil, fmt.Errorf("error get location %q: %w", locationName, err)
    }

    // 2. Достаем точный UUID этой локации
    var locationUUID string
    for _, loc := range *locations {
       if strings.EqualFold(loc.Name, locationName) || loc.Name == locationName {
          locationUUID = loc.UUID
          break
       }
    }

    if locationUUID == "" {
       return nil, fmt.Errorf("location %q not found", locationName)
    }

    // 3. Запрашиваем расписание по UUID локации
    allSchedule, err := s.repo.ScheduleRepository.GetScheduleByLocationUUID(locationUUID, isSession)
    if err != nil {
       return nil, fmt.Errorf("error get schedule: %w", err)
    }

    // 4. Пакуем в неделю
    return makeWeek(allSchedule), nil
}

func makeWeek(schedule *[]models.GetSchedule) *models.Week {
	week := &models.Week{}

	timeToPairNum := map[string]int{
		"09:00:00": 1,
		"10:40:00": 2,
		"12:20:00": 3,
		"14:30:00": 4,
		"16:10:00": 5,
		"17:50:00": 6,
		"19:30:00": 7,
	}

	for _, s := range *schedule {
		pairNum := timeToPairNum[s.StartTime.Format("15:04:05")]

		pair := &models.Pair{
			Group:       s.Group,
			Subject:     s.Subject,
			SubjectType: s.SubjectType,
			Location:    s.Location,
			Teachers:    s.Teachers,
			Rooms:       s.Rooms,
			StartDate:   s.StartDate.Format("2006-01-02"),
			EndDate:     s.EndDate.Format("2006-01-02"),
			Link:        s.Link,
		}
		addPairToWeek(week, s.Weekday, pairNum, pair)
	}

	return week
}

func addPairToWeek(week *models.Week, weekday int, pairNum int, pair *models.Pair) {
	var day **models.Day
	switch weekday {
	case 1:
		day = &week.Monday
	case 2:
		day = &week.Tuesday
	case 3:
		day = &week.Wednesday
	case 4:
		day = &week.Thursday
	case 5:
		day = &week.Friday
	case 6:
		day = &week.Saturday
	default:
		return
	}

	if *day == nil {
		*day = &models.Day{}
	}

	var slot **[]models.Pair
	switch pairNum {
	case 1:
		slot = &(*day).First
	case 2:
		slot = &(*day).Second
	case 3:
		slot = &(*day).Third
	case 4:
		slot = &(*day).Fourth
	case 5:
		slot = &(*day).Fifth
	case 6:
		slot = &(*day).Sixth
	case 7:
		slot = &(*day).Seventh
	default:
		return
	}

	if *slot == nil {
		empty := make([]models.Pair, 0)
		*slot = &empty
	}

	**slot = append(**slot, *pair)
}
func (s *ScheduleService) GetAllSchedule(isSession bool) (*[]models.GetSchedule, error) {
	allSchedule, err := s.repo.ScheduleRepository.GetAllSchedule(isSession)
	if err != nil {
		return nil, fmt.Errorf("error get all schedule: %w", err)
	}

	return allSchedule, nil
}