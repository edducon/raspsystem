package repository

import (
	"context"
	"raspyx2/internal/models"
	"raspyx2/internal/repository/catalog"

	"github.com/jackc/pgx/v5/pgxpool"
)

type CatalogRepository interface {
	ListBuildings(ctx context.Context) ([]models.Building, error)
	GetBuilding(ctx context.Context, id int32) (*models.Building, error)
	CreateBuilding(ctx context.Context, input models.BuildingCreateRequest) (*models.Building, error)
	UpdateBuilding(ctx context.Context, id int32, input models.BuildingUpdateRequest) (*models.Building, error)
	DeleteBuilding(ctx context.Context, id int32) error

	ListCampuses(ctx context.Context, buildingID *int32) ([]models.Campus, error)
	GetCampus(ctx context.Context, id int32) (*models.Campus, error)
	CreateCampus(ctx context.Context, input models.CampusCreateRequest) (*models.Campus, error)
	UpdateCampus(ctx context.Context, id int32, input models.CampusUpdateRequest) (*models.Campus, error)
	DeleteCampus(ctx context.Context, id int32) error

	ListRooms(ctx context.Context, campusID *int32) ([]models.Room, error)
	GetRoom(ctx context.Context, id int32) (*models.Room, error)
	CreateRoom(ctx context.Context, input models.RoomCreateRequest) (*models.Room, error)
	UpdateRoom(ctx context.Context, id int32, input models.RoomUpdateRequest) (*models.Room, error)
	DeleteRoom(ctx context.Context, id int32) error

	ListDirections(ctx context.Context) ([]models.Direction, error)
	GetDirection(ctx context.Context, id int32) (*models.Direction, error)
	CreateDirection(ctx context.Context, input models.DirectionCreateRequest) (*models.Direction, error)
	UpdateDirection(ctx context.Context, id int32, input models.DirectionUpdateRequest) (*models.Direction, error)
	DeleteDirection(ctx context.Context, id int32) error

	ListGroups(ctx context.Context, filter models.GroupFilter) ([]models.Group, error)
	GetGroup(ctx context.Context, id int32) (*models.Group, error)
	CreateGroup(ctx context.Context, input models.GroupCreateRequest) (*models.Group, error)
	UpdateGroup(ctx context.Context, id int32, input models.GroupUpdateRequest) (*models.Group, error)
	DeleteGroup(ctx context.Context, id int32) error

	ListSubjects(ctx context.Context) ([]models.Subject, error)
	GetSubject(ctx context.Context, id int32) (*models.Subject, error)
	CreateSubject(ctx context.Context, input models.SubjectCreateRequest) (*models.Subject, error)
	UpdateSubject(ctx context.Context, id int32, input models.SubjectUpdateRequest) (*models.Subject, error)
	DeleteSubject(ctx context.Context, id int32) error

	ListSubjectTypes(ctx context.Context) ([]models.SubjectType, error)
	GetSubjectType(ctx context.Context, id int32) (*models.SubjectType, error)
	CreateSubjectType(ctx context.Context, input models.SubjectTypeCreateRequest) (*models.SubjectType, error)
	UpdateSubjectType(ctx context.Context, id int32, input models.SubjectTypeUpdateRequest) (*models.SubjectType, error)
	DeleteSubjectType(ctx context.Context, id int32) error
}

type Repository struct {
	CatalogRepository
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{
		CatalogRepository: catalog.NewRepository(pool),
	}
}
