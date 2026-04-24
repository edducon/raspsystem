package scheduleParser

import (
	"encoding/json"
	"fmt"
	"github.com/google/go-cmp/cmp"
	"io"
	"net/http"
	"raspyx2/internal/models"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

func (p *ScheduleParser) ParseGroups() ([]string, error) {
	req, err := http.NewRequest("GET", "https://rasp.dmami.ru/", nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Referer", "https://rasp.dmami.ru/")

	resp, err := p.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	re := regexp.MustCompile(`\d{2}[0-9a-zA-Zа-яА-Я]-\d{3,4}(\s[a-zA-Zа-яА-Я]{3})?`)
	matches := re.FindAll(raw, -1)

	gm := make(map[string]int)
	for _, m := range matches {
		if _, ok := gm[string(m)]; !ok {
			gm[string(m)] = 1
		}
	}

	groups := make([]string, 0, len(gm))
	for group := range gm {
		groups = append(groups, p.RemoveTrash(group))
	}

	return groups, nil
}

func (p *ScheduleParser) ParseSubjects(data *models.ParseScheduleResponse) {
	cache := make(map[string]bool)

	for _, day := range data.Grid {
		for _, pair := range day {
			for _, pairData := range pair {
				select {
				case <-p.Ctx.Done():
					return
				default:
					pairData.Sbj = p.RemoveTrash(pairData.Sbj)
					if _, ok := cache[pairData.Sbj]; ok {
						continue
					}

					_, err := p.Services.SubjectsService.CreateSubject(&models.AddSubjectRequest{Name: pairData.Sbj})
					if err != nil && !strings.Contains(err.Error(), "exists") {
						p.Log.Error(fmt.Sprintf("error adding subject %s to db: %s", pairData.Sbj, err.Error()))
					} else {
						cache[pairData.Sbj] = true
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) ParseTeachers(data *models.ParseScheduleResponse) {
	cache := make(map[string]bool)

	for _, day := range data.Grid {
		for _, pair := range day {
			for _, pairData := range pair {
				select {
				case <-p.Ctx.Done():
					return
				default:
					for _, teacher := range pairData.Teachers {
						t, err := p.clearTeacher(teacher.Name)
						if err != nil {
							p.Log.Error(err.Error())
							continue
						}

						tn := strings.TrimSpace(fmt.Sprintf("%s %s %s", t.SecondName, t.FirstName, t.MiddleName))
						if _, ok := cache[tn]; ok {
							continue
						}

						_, err = p.Services.TeachersService.GetTeacherByFio(tn)
						if err == nil {
							cache[tn] = true
							continue
						}

						_, err = p.Services.TeachersService.CreateTeacher(&models.AddTeacherRequest{
							FirstName:  t.FirstName,
							SecondName: t.SecondName,
							MiddleName: t.MiddleName,
						})
						if err != nil && !strings.Contains(err.Error(), "exists") {
							p.Log.Error(fmt.Sprintf("error adding teacher %s to db: %s", tn, err.Error()))
						} else {
							cache[tn] = true
						}
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) ParseRooms(data *models.ParseScheduleResponse) {
	cache := make(map[string]bool)

	for _, day := range data.Grid {
		for _, pair := range day {
			for _, pairData := range pair {
				select {
				case <-p.Ctx.Done():
					return
				default:
					for _, room := range pairData.Auditories {
						room.Title = p.RemoveTrash(room.Title)
						if _, ok := cache[room.Title]; ok {
							continue
						}

						_, err := p.Services.RoomsService.CreateRoom(&models.AddRoomRequest{
							Number: room.Title,
						})
						if err != nil && !strings.Contains(err.Error(), "exists") {
							p.Log.Error(fmt.Sprintf("error adding room %s to db: %s", room.Title, err.Error()))
						} else {
							cache[room.Title] = true
						}
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) ParseLocations(data *models.ParseScheduleResponse) {
	cache := make(map[string]bool)

	for _, day := range data.Grid {
		for _, pair := range day {
			for _, pairData := range pair {
				select {
				case <-p.Ctx.Done():
					return
				default:
					location := p.RemoveTrash(pairData.Location)
					if _, ok := cache[location]; ok {
						continue
					}

					_, err := p.Services.LocationsService.CreateLocation(&models.AddLocationRequest{
						Name: location,
					})
					if err != nil && !strings.Contains(err.Error(), "exists") {
						p.Log.Error(fmt.Sprintf("error adding location %s to db: %s", location, err.Error()))
					} else {
						cache[location] = true
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) ParseSubjectTypes(data *models.ParseScheduleResponse) {
	cache := make(map[string]bool)

	for _, day := range data.Grid {
		for _, pair := range day {
			for _, pairData := range pair {
				select {
				case <-p.Ctx.Done():
					return
				default:
					pairData.Type = p.RemoveTrash(pairData.Type)
					if _, ok := cache[pairData.Type]; ok {
						continue
					}

					_, err := p.Services.SubjectTypesService.CreateSubjectType(&models.AddSubjectTypeRequest{Type: pairData.Type})
					if err != nil && !strings.Contains(err.Error(), "exists") {
						p.Log.Error(fmt.Sprintf("error adding subject type %s to db: %s", pairData.Type, err.Error()))
					} else {
						cache[pairData.Type] = true
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) ParseSchedules(groupNumber string, data *models.ParseScheduleResponse) {
	if data.IsSession {
		var err error
		data.Grid, err = sessionToNormalGrid(data.Grid)
		if err != nil {
			p.Log.Error(err.Error())
			return
		}
	}

	week, err := p.Services.ScheduleService.GetScheduleByGroupNumber(groupNumber, data.IsSession)
	if err != nil || week == nil {
		week = &models.Week{
			Monday:    initDay(),
			Tuesday:   initDay(),
			Wednesday: initDay(),
			Thursday:  initDay(),
			Friday:    initDay(),
			Saturday:  initDay(),
		}
	}

	select {
	case <-p.Ctx.Done():
		return
	default:
		for dayNum, day := range data.Grid {
			for pairNum, pairs := range day {
				// pairs from rasp.dmami.ru -> []models.Pair
				mappedPairs := make([]models.Pair, 0)
				for _, pair := range pairs {
					mappedPairs = append(mappedPairs, *p.mapLessonToPair(groupNumber, &pair))
				}

				// if it session dayNum: 2026-01-12 -> 1 (Monday)
				if data.IsSession && !strings.Contains("123456", dayNum) {
					dayNum, err = sessionDateToDayNum(dayNum)
					if err != nil {
						p.Log.Error(err.Error())
						break
					} else if dayNum == "" { // if it is sunday
						break
					}
				}

				// pairs from db -> []models.Pair
				dbPairs := getPair(pairNum, getDay(dayNum, week))

				// clear uuids from pairs from db because pairs from rasp.dmami.ru does not have it
				clearUUIDs(dbPairs)

				if len(*dbPairs) == 0 && len(mappedPairs) == 0 { // if there is no pairs
					continue
				} else if len(*dbPairs) == 0 && len(mappedPairs) > 0 { // if there are no pairs in the db, but it is in rasp.dmami.ru
					for _, pair := range pairs {
						err = p.createSchedule(groupNumber, pairNum, dayNum, data.IsSession, &pair)
						if err != nil {
							p.Log.Error(err.Error())
						}
					}
					continue
				} else if len(*dbPairs) > 0 && len(mappedPairs) == 0 { // if there are pairs in the db, but they are not in rasp.dmami.ru
					weekday, err := strconv.ParseInt(dayNum, 10, 0)
					if err != nil {
						p.Log.Error(err.Error())
						continue
					}
					err = p.deleteSchedule(groupNumber, pairNum, int(weekday), data.IsSession)
					if err != nil {
						p.Log.Error(err.Error())
					}
					continue
				}

				// sorting pairs for correct comparison
				sortPairs(dbPairs)
				sortPairs(&mappedPairs)

				// if the pairs from the db are not equal to the pairs from rasp.dmami.ru
				if !cmp.Equal(*dbPairs, mappedPairs) {
					d, _ := json.MarshalIndent(*dbPairs, "", "\t")
					m, _ := json.MarshalIndent(mappedPairs, "", "\t")
					fmt.Println("db", string(d))
					fmt.Println("mp", string(m))
					fmt.Println(cmp.Diff(*dbPairs, mappedPairs))
					if dbPairs != nil && len(*dbPairs) > 0 {
						weekday, err := strconv.ParseInt(dayNum, 10, 0)
						if err != nil {
							p.Log.Error(err.Error())
							continue
						}
						err = p.deleteSchedule(groupNumber, pairNum, int(weekday), data.IsSession)
						if err != nil {
							p.Log.Error(err.Error())
						}
					}

					for _, pair := range pairs {
						err = p.createSchedule(groupNumber, pairNum, dayNum, data.IsSession, &pair)
						if err != nil {
							p.Log.Error(err.Error())
						}
					}
				}
			}
		}
	}
}

func (p *ScheduleParser) mapLessonToPair(groupNumber string, lesson *models.Lesson) *models.Pair {
	teachers := make([]models.GetTeacherResponse, 0)
	rooms := make([]models.Room, 0)

	for _, teacher := range lesson.Teachers {
		teachers = append(teachers, models.GetTeacherResponse{
			FullName: strings.Join(strings.Fields(p.RemoveTrash(teacher.Name)), " "),
		})
	}
	sort.Slice(teachers, func(i, j int) bool {
		return teachers[i].FullName < teachers[j].FullName
	})

	for _, room := range lesson.Auditories {
		rooms = append(rooms, models.Room{
			Number: p.RemoveTrash(room.Title),
		})
	}
	sort.Slice(rooms, func(i, j int) bool {
		return rooms[i].Number < rooms[j].Number
	})

	var link string
	if len(lesson.Auditories) > 0 {
		link = getLinkFromHTML(lesson.Auditories[0].Title)
	} else {
		link = ""
	}

	pair := &models.Pair{
		Group:       &models.Group{Number: groupNumber},
		Subject:     &models.Subject{Name: p.RemoveTrash(lesson.Sbj)},
		SubjectType: &models.SubjectType{Type: p.RemoveTrash(lesson.Type)},
		Location:    &models.Location{Name: p.RemoveTrash(lesson.Location)},
		Teachers:    &teachers,
		Rooms:       &rooms,
		StartDate:   lesson.Df,
		EndDate:     lesson.Dt,
		Link:        link,
	}

	return pair
}

func getLinkFromHTML(html string) string {
	htmlRegex := regexp.MustCompile(`['"].*?['"]`)
	links := htmlRegex.FindAllString(html, -1)

	for _, link := range links {
		if strings.Contains(link, "http") {
			return link[1 : len(link)-1]
		}
	}

	return ""
}

func getDay(dayNum string, week *models.Week) *models.Day {
	switch dayNum {
	case "1":
		return week.Monday
	case "2":
		return week.Tuesday
	case "3":
		return week.Wednesday
	case "4":
		return week.Thursday
	case "5":
		return week.Friday
	case "6":
		return week.Saturday
	default:
		return &models.Day{}
	}
}

func getPair(pairNum string, day *models.Day) *[]models.Pair {
	pair := &[]models.Pair{}
	if day == nil {
		return pair
	}

	switch pairNum {
	case "1":
		if day.First != nil {
			pair = day.First
		}
	case "2":
		if day.Second != nil {
			pair = day.Second
		}
	case "3":
		if day.Third != nil {
			pair = day.Third
		}
	case "4":
		if day.Fourth != nil {
			pair = day.Fourth
		}
	case "5":
		if day.Fifth != nil {
			pair = day.Fifth
		}
	case "6":
		if day.Sixth != nil {
			pair = day.Sixth
		}
	case "7":
		if day.Seventh != nil {
			pair = day.Seventh
		}
	}

	for i := range *pair {
		p := &(*pair)[i]

		if p.Teachers != nil {
			sort.Slice(*p.Teachers, func(i, j int) bool {
				return (*p.Teachers)[i].FullName < (*p.Teachers)[j].FullName
			})
		}

		if p.Rooms != nil {
			sort.Slice(*p.Rooms, func(i, j int) bool {
				return (*p.Rooms)[i].Number < (*p.Rooms)[j].Number
			})
		}
	}

	sort.Slice(*pair, func(i, j int) bool {
		return (*pair)[i].StartDate < (*pair)[j].StartDate
	})

	return pair
}

func initDay() *models.Day {
	return &models.Day{
		First:   &[]models.Pair{},
		Second:  &[]models.Pair{},
		Third:   &[]models.Pair{},
		Fourth:  &[]models.Pair{},
		Fifth:   &[]models.Pair{},
		Sixth:   &[]models.Pair{},
		Seventh: &[]models.Pair{},
	}
}

func pairNumToSTET(pair string) (string, string) {
	switch pair {
	case "1":
		return "09:00:00", "10:30:00"
	case "2":
		return "10:40:00", "12:10:00"
	case "3":
		return "12:20:00", "13:50:00"
	case "4":
		return "14:30:00", "16:00:00"
	case "5":
		return "16:10:00", "17:40:00"
	case "6":
		return "17:50:00", "19:20:00"
	case "7":
		return "19:30:00", "21:00:00"
	default:
		return "", ""
	}
}

func (p *ScheduleParser) deleteSchedule(groupNumber, pairNum string, weekday int, isSession bool) error {
	group, err := p.Services.GroupsService.GetGroupByNumber(groupNumber)
	if err != nil {
		return err
	}

	st, _ := pairNumToSTET(pairNum)

	err = p.Services.DeleteScheduleByFilters(&models.DeleteScheduleFilters{
		GroupUUID: group.UUID,
		StartTime: st,
		Weekday:   &weekday,
		IsSession: &isSession,
	})

	return err
}

func (p *ScheduleParser) createSchedule(groupNumber, pairNum, dayNum string, isSession bool, pair *models.Lesson) error {
	group, err := p.Services.GroupsService.GetGroupByNumber(p.RemoveTrash(groupNumber))
	if err != nil {
		return err
	}

	subject, err := p.Services.SubjectsService.GetSubjectByName(p.RemoveTrash(pair.Sbj))
	if err != nil {
		return err
	}

	subjectType, err := p.Services.SubjectTypesService.GetSubjectTypeByType(p.RemoveTrash(pair.Type))
	if err != nil {
		return err
	}

	location, err := p.Services.LocationsService.GetLocationByName(p.RemoveTrash(pair.Location))
	if err != nil {
		return err
	}

	var teachers []models.AddTeacherSchedule
	for _, t := range pair.Teachers {
		teacher, err := p.clearTeacher(t.Name)
		if err != nil {
			p.Log.Error(err.Error())
			continue
		}

		teacher, err = p.Services.TeachersService.GetTeacherByFio(strings.TrimSpace(fmt.Sprintf("%s %s %s",
			teacher.SecondName, teacher.FirstName, teacher.MiddleName,
		)))
		if err != nil {
			p.Log.Error(err.Error())
			continue
		}

		teachers = append(teachers, models.AddTeacherSchedule{TeacherUUID: teacher.UUID})
	}

	var rooms []models.AddRoomSchedule
	for _, r := range pair.Auditories {
		room, err := p.Services.RoomsService.GetRoomByNumber(p.RemoveTrash(r.Title))
		if err != nil {
			p.Log.Error(err.Error())
			continue
		}

		rooms = append(rooms, models.AddRoomSchedule{RoomUUID: room.UUID})
	}

	st, et := pairNumToSTET(pairNum)

	var weekday int64

	weekday, err = strconv.ParseInt(dayNum, 10, 0)
	if err != nil {
		return err
	}

	var link string
	if len(pair.Auditories) > 0 {
		link = getLinkFromHTML(pair.Auditories[0].Title)
	}

	_, err = p.Services.ScheduleService.CreateSchedule(&models.AddScheduleRequest{
		GroupUUID:       group.UUID,
		SubjectUUID:     subject.UUID,
		SubjectTypeUUID: subjectType.UUID,
		LocationUUID:    location.UUID,
		TeachersUUID:    teachers,
		RoomsUUID:       rooms,
		StartTime:       st,
		EndTime:         et,
		StartDate:       pair.Df,
		EndDate:         pair.Dt,
		Weekday:         int(weekday),
		Link:            link,
		IsSession:       isSession,
	})

	return err
}

func (p *ScheduleParser) clearTeacher(fio string) (*models.Teacher, error) {
	fio = p.RemoveTrash(fio)

	splitedTeacher := strings.Split(fio, " ")
	for i, str := range splitedTeacher {
		if str == "" {
			splitedTeacher = append(splitedTeacher[:i], splitedTeacher[i+1:]...)
		}
	}

	if len(splitedTeacher) < 1 {
		return nil, fmt.Errorf("invalid fio")
	}

	splitedTeacher = append(splitedTeacher, []string{" ", " "}...)

	return &models.Teacher{
		FirstName:  splitedTeacher[1],
		SecondName: splitedTeacher[0],
		MiddleName: strings.TrimSpace(strings.Join(splitedTeacher[2:], " ")),
	}, nil
}

func clearUUIDs(pairs *[]models.Pair) {
	for i := range *pairs {
		pair := &(*pairs)[i]

		pair.Group.UUID = ""
		pair.Subject.UUID = ""
		pair.SubjectType.UUID = ""
		pair.Location.UUID = ""

		if pair.Teachers != nil {
			newt := make([]models.GetTeacherResponse, len(*pair.Teachers))
			for j, t := range *pair.Teachers {
				newt[j] = models.GetTeacherResponse{FullName: t.FullName}
			}
			pair.Teachers = &newt
		}

		if pair.Rooms != nil {
			newr := make([]models.Room, len(*pair.Rooms))
			for j, r := range *pair.Rooms {
				newr[j] = models.Room{Number: r.Number}
			}
			pair.Rooms = &newr
		}
	}
}

func sortPairs(pairs *[]models.Pair) {
	if *pairs != nil {
		sort.Slice(*pairs, func(i, j int) bool {
			if (*pairs)[i].StartDate != (*pairs)[j].StartDate {
				return (*pairs)[i].StartDate < (*pairs)[j].StartDate
			} else if (*pairs)[i].EndDate != (*pairs)[j].EndDate {
				return (*pairs)[i].EndDate < (*pairs)[j].EndDate
			} else if (*pairs)[i].SubjectType.Type != (*pairs)[j].SubjectType.Type {
				return (*pairs)[i].SubjectType.Type < (*pairs)[j].SubjectType.Type
			}

			return (*pairs)[i].Subject.Name < (*pairs)[j].Subject.Name
		})
	}
}

func sessionDateToDayNum(dayNum string) (string, error) {
	parsedTime, err := time.Parse("2006-01-02", dayNum)
	if err != nil {
		return "", err
	}

	dayNum = strconv.FormatInt(int64(parsedTime.Weekday()), 10)
	if dayNum == "0" {
		return "", nil
	}

	return dayNum, nil
}

func sessionToNormalGrid(grid map[string]map[string][]models.Lesson) (map[string]map[string][]models.Lesson, error) {
	newGrid := makeGrid()
	for date, day := range grid {
		dayNum, err := sessionDateToDayNum(date)
		if err != nil {
			return nil, err
		}
		if dayNum == "" {
			continue
		}

		for pairNum, _ := range day {
			if _, ok := newGrid[dayNum][pairNum]; !ok {
				newGrid[dayNum][pairNum] = grid[date][pairNum]
			} else {
				newGrid[dayNum][pairNum] = append(newGrid[dayNum][pairNum], grid[date][pairNum]...)
			}
		}
	}

	return newGrid, nil
}

func makeGrid() map[string]map[string][]models.Lesson {
	grid := make(map[string]map[string][]models.Lesson)
	for _, dayNum := range []string{"1", "2", "3", "4", "5", "6"} {
		if grid[dayNum] == nil {
			grid[dayNum] = make(map[string][]models.Lesson)
		}
		for _, pairNum := range []string{"1", "2", "3", "4", "5", "6", "7"} {
			grid[dayNum][pairNum] = make([]models.Lesson, 0)
		}
	}

	return grid
}
