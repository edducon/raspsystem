package catalog

import (
	"context"
	"strings"

	"raspyx2/internal/models"
	"raspyx2/internal/repository"
)

type Service struct {
	repo *repository.Repository
}

func NewService(repo *repository.Repository) *Service {
	return &Service{repo: repo}
}

func (s *Service) ListBuildings(ctx context.Context) ([]models.Building, error) {
	return s.repo.ListBuildings(ctx)
}

func (s *Service) GetBuilding(ctx context.Context, id int32) (*models.Building, error) {
	return s.repo.GetBuilding(ctx, id)
}

func (s *Service) CreateBuilding(ctx context.Context, input models.BuildingCreateRequest) (*models.Building, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateBuilding(ctx, input)
}

func (s *Service) UpdateBuilding(ctx context.Context, id int32, input models.BuildingUpdateRequest) (*models.Building, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateBuilding(ctx, id, input)
}

func (s *Service) DeleteBuilding(ctx context.Context, id int32) error {
	return s.repo.DeleteBuilding(ctx, id)
}

func (s *Service) ListCampuses(ctx context.Context, buildingID *int32) ([]models.Campus, error) {
	return s.repo.ListCampuses(ctx, buildingID)
}

func (s *Service) GetCampus(ctx context.Context, id int32) (*models.Campus, error) {
	return s.repo.GetCampus(ctx, id)
}

func (s *Service) CreateCampus(ctx context.Context, input models.CampusCreateRequest) (*models.Campus, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateCampus(ctx, input)
}

func (s *Service) UpdateCampus(ctx context.Context, id int32, input models.CampusUpdateRequest) (*models.Campus, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateCampus(ctx, id, input)
}

func (s *Service) DeleteCampus(ctx context.Context, id int32) error {
	return s.repo.DeleteCampus(ctx, id)
}

func (s *Service) ListRooms(ctx context.Context, campusID *int32) ([]models.Room, error) {
	return s.repo.ListRooms(ctx, campusID)
}

func (s *Service) GetRoom(ctx context.Context, id int32) (*models.Room, error) {
	return s.repo.GetRoom(ctx, id)
}

func (s *Service) CreateRoom(ctx context.Context, input models.RoomCreateRequest) (*models.Room, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateRoom(ctx, input)
}

func (s *Service) UpdateRoom(ctx context.Context, id int32, input models.RoomUpdateRequest) (*models.Room, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateRoom(ctx, id, input)
}

func (s *Service) DeleteRoom(ctx context.Context, id int32) error {
	return s.repo.DeleteRoom(ctx, id)
}

func (s *Service) ListDirections(ctx context.Context) ([]models.Direction, error) {
	return s.repo.ListDirections(ctx)
}

func (s *Service) GetDirection(ctx context.Context, id int32) (*models.Direction, error) {
	return s.repo.GetDirection(ctx, id)
}

func (s *Service) CreateDirection(ctx context.Context, input models.DirectionCreateRequest) (*models.Direction, error) {
	input.Name = strings.TrimSpace(input.Name)
	input.Code = strings.TrimSpace(input.Code)
	return s.repo.CreateDirection(ctx, input)
}

func (s *Service) UpdateDirection(ctx context.Context, id int32, input models.DirectionUpdateRequest) (*models.Direction, error) {
	input.Name = strings.TrimSpace(input.Name)
	input.Code = strings.TrimSpace(input.Code)
	return s.repo.UpdateDirection(ctx, id, input)
}

func (s *Service) DeleteDirection(ctx context.Context, id int32) error {
	return s.repo.DeleteDirection(ctx, id)
}

func (s *Service) ListGroups(ctx context.Context, filter models.GroupFilter) ([]models.Group, error) {
	return s.repo.ListGroups(ctx, filter)
}

func (s *Service) GetGroup(ctx context.Context, id int32) (*models.Group, error) {
	return s.repo.GetGroup(ctx, id)
}

func (s *Service) CreateGroup(ctx context.Context, input models.GroupCreateRequest) (*models.Group, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateGroup(ctx, input)
}

func (s *Service) UpdateGroup(ctx context.Context, id int32, input models.GroupUpdateRequest) (*models.Group, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateGroup(ctx, id, input)
}

func (s *Service) DeleteGroup(ctx context.Context, id int32) error {
	return s.repo.DeleteGroup(ctx, id)
}

func (s *Service) ListSubjects(ctx context.Context) ([]models.Subject, error) {
	return s.repo.ListSubjects(ctx)
}

func (s *Service) GetSubject(ctx context.Context, id int32) (*models.Subject, error) {
	return s.repo.GetSubject(ctx, id)
}

func (s *Service) CreateSubject(ctx context.Context, input models.SubjectCreateRequest) (*models.Subject, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateSubject(ctx, input)
}

func (s *Service) UpdateSubject(ctx context.Context, id int32, input models.SubjectUpdateRequest) (*models.Subject, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateSubject(ctx, id, input)
}

func (s *Service) DeleteSubject(ctx context.Context, id int32) error {
	return s.repo.DeleteSubject(ctx, id)
}

func (s *Service) ListSubjectTypes(ctx context.Context) ([]models.SubjectType, error) {
	return s.repo.ListSubjectTypes(ctx)
}

func (s *Service) GetSubjectType(ctx context.Context, id int32) (*models.SubjectType, error) {
	return s.repo.GetSubjectType(ctx, id)
}

func (s *Service) CreateSubjectType(ctx context.Context, input models.SubjectTypeCreateRequest) (*models.SubjectType, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.CreateSubjectType(ctx, input)
}

func (s *Service) UpdateSubjectType(ctx context.Context, id int32, input models.SubjectTypeUpdateRequest) (*models.SubjectType, error) {
	input.Name = strings.TrimSpace(input.Name)
	return s.repo.UpdateSubjectType(ctx, id, input)
}

func (s *Service) DeleteSubjectType(ctx context.Context, id int32) error {
	return s.repo.DeleteSubjectType(ctx, id)
}
