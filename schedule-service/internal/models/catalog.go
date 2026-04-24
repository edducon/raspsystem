package models

type Building struct {
	ID        int32   `json:"id"`
	Name      string  `json:"name"`
	ShortName *string `json:"short_name,omitempty"`
	Address   *string `json:"address,omitempty"`
}

type BuildingCreateRequest struct {
	Name      string  `json:"name" binding:"required"`
	ShortName *string `json:"short_name"`
	Address   *string `json:"address"`
}

type BuildingUpdateRequest = BuildingCreateRequest

type Campus struct {
	ID         int32  `json:"id"`
	BuildingID int32  `json:"building_id"`
	Name       string `json:"name"`
	Floor      *int16 `json:"floor,omitempty"`
}

type CampusCreateRequest struct {
	BuildingID int32  `json:"building_id" binding:"required"`
	Name       string `json:"name" binding:"required"`
	Floor      *int16 `json:"floor"`
}

type CampusUpdateRequest = CampusCreateRequest

type Room struct {
	ID       int32  `json:"id"`
	CampusID int32  `json:"campus_id"`
	Name     string `json:"name"`
	Capacity *int16 `json:"capacity,omitempty"`
}

type RoomCreateRequest struct {
	CampusID int32  `json:"campus_id" binding:"required"`
	Name     string `json:"name" binding:"required"`
	Capacity *int16 `json:"capacity"`
}

type RoomUpdateRequest = RoomCreateRequest

type Direction struct {
	ID           int32  `json:"id"`
	Name         string `json:"name"`
	Code         string `json:"code"`
	DepartmentID int32  `json:"department_id"`
}

type DirectionCreateRequest struct {
	Name         string `json:"name" binding:"required"`
	Code         string `json:"code" binding:"required"`
	DepartmentID int32  `json:"department_id" binding:"required"`
}

type DirectionUpdateRequest = DirectionCreateRequest

type Group struct {
	ID            int32  `json:"id"`
	Name          string `json:"name"`
	AdmissionYear int16  `json:"admission_year"`
	StudyForm     int16  `json:"study_form"`
	DirectionID   int32  `json:"direction_id"`
	Stream        int16  `json:"stream"`
}

type GroupCreateRequest struct {
	Name          string `json:"name" binding:"required"`
	AdmissionYear int16  `json:"admission_year" binding:"required"`
	StudyForm     int16  `json:"study_form" binding:"required"`
	DirectionID   int32  `json:"direction_id" binding:"required"`
	Stream        int16  `json:"stream" binding:"required"`
}

type GroupUpdateRequest = GroupCreateRequest

type GroupFilter struct {
	DirectionID   *int32
	AdmissionYear *int16
}

type Subject struct {
	ID        int32   `json:"id"`
	Name      string  `json:"name"`
	ShortName *string `json:"short_name,omitempty"`
}

type SubjectCreateRequest struct {
	Name      string  `json:"name" binding:"required"`
	ShortName *string `json:"short_name"`
}

type SubjectUpdateRequest = SubjectCreateRequest

type SubjectType struct {
	ID        int32   `json:"id"`
	Name      string  `json:"name"`
	ShortName *string `json:"short_name,omitempty"`
	IsOnline  bool    `json:"is_online"`
}

type SubjectTypeCreateRequest struct {
	Name      string  `json:"name" binding:"required"`
	ShortName *string `json:"short_name"`
	IsOnline  bool    `json:"is_online"`
}

type SubjectTypeUpdateRequest = SubjectTypeCreateRequest
