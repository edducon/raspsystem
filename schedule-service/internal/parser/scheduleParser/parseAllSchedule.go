package scheduleParser

import (
	"fmt"
	"raspyx2/internal/models"
	"strings"
)

func (p *ScheduleParser) Parse() {
	groups, err := p.ParseGroups()
	if err != nil {
		p.Log.Error(err.Error())
		return
	}

	sumGroups := len(groups)

	for _, g := range groups {
		_, err = p.Services.GroupsService.CreateGroup(&models.AddGroupRequest{Number: g})
		if err != nil && !strings.Contains(err.Error(), "already exists") {
			p.Log.Error(err.Error())
		}
	}

	//r, err := p.ParseGroupSchedule(&models.ParseGroupScheduleData{Group: "221-351", IsSession: 1})
	//if err != nil {
	//	p.Log.Error(err.Error())
	//	return
	//}
	//
	//p.ParseLocations(r)
	//p.ParseRooms(r)
	//p.ParseSubjects(r)
	//p.ParseSubjectTypes(r)
	//p.ParseTeachers(r)
	//p.ParseSchedules("221-351", r)

	pool := make(chan interface{}, 5)

	for i, g := range groups {
		pool <- 1
		go func() {
			p.Log.Debug(fmt.Sprintf("%d/%d %s 0", i+1, sumGroups, g))
			r, err := p.ParseGroupSchedule(&models.ParseGroupScheduleData{Group: g, IsSession: 0})
			if err != nil {
				p.Log.Error(err.Error())
				<-pool
				return
			}

			p.ParseLocations(r)
			p.ParseRooms(r)
			p.ParseSubjects(r)
			p.ParseSubjectTypes(r)
			p.ParseTeachers(r)
			p.ParseSchedules(g, r)

			<-pool
		}()
	}

	for i, g := range groups {
		pool <- 1
		go func() {
			p.Log.Debug(fmt.Sprintf("%d/%d %s 1", i+1, sumGroups, g))
			r, err := p.ParseGroupSchedule(&models.ParseGroupScheduleData{Group: g, IsSession: 1})
			if err != nil {
				p.Log.Error(err.Error())
				<-pool
				return
			}

			p.ParseLocations(r)
			p.ParseRooms(r)
			p.ParseSubjects(r)
			p.ParseSubjectTypes(r)
			p.ParseTeachers(r)
			p.ParseSchedules(g, r)

			<-pool
		}()
	}
}
