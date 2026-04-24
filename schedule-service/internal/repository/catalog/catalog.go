package catalog

import (
	"context"
	"strconv"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"raspyx2/internal/models"
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

func (r *Repository) ListBuildings(ctx context.Context) ([]models.Building, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, name, short_name, address
		FROM buildings
		ORDER BY name, id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Building, error) {
		var item models.Building
		err := row.Scan(&item.ID, &item.Name, &item.ShortName, &item.Address)
		return item, err
	})
}

func (r *Repository) GetBuilding(ctx context.Context, id int32) (*models.Building, error) {
	var item models.Building
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, short_name, address
		FROM buildings
		WHERE id = $1
	`, id).Scan(&item.ID, &item.Name, &item.ShortName, &item.Address)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateBuilding(ctx context.Context, input models.BuildingCreateRequest) (*models.Building, error) {
	var item models.Building
	err := r.pool.QueryRow(ctx, `
		INSERT INTO buildings (name, short_name, address)
		VALUES ($1, $2, $3)
		RETURNING id, name, short_name, address
	`, input.Name, normalizeNullableString(input.ShortName), normalizeNullableString(input.Address)).
		Scan(&item.ID, &item.Name, &item.ShortName, &item.Address)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateBuilding(ctx context.Context, id int32, input models.BuildingUpdateRequest) (*models.Building, error) {
	var item models.Building
	err := r.pool.QueryRow(ctx, `
		UPDATE buildings
		SET name = $2, short_name = $3, address = $4
		WHERE id = $1
		RETURNING id, name, short_name, address
	`, id, input.Name, normalizeNullableString(input.ShortName), normalizeNullableString(input.Address)).
		Scan(&item.ID, &item.Name, &item.ShortName, &item.Address)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteBuilding(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "buildings", id)
}

func (r *Repository) ListCampuses(ctx context.Context, buildingID *int32) ([]models.Campus, error) {
	query := `
		SELECT id, building_id, name, floor
		FROM campuses
	`
	args := []any{}
	if buildingID != nil {
		query += ` WHERE building_id = $1`
		args = append(args, *buildingID)
	}
	query += ` ORDER BY name, id`
	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Campus, error) {
		var item models.Campus
		err := row.Scan(&item.ID, &item.BuildingID, &item.Name, &item.Floor)
		return item, err
	})
}

func (r *Repository) GetCampus(ctx context.Context, id int32) (*models.Campus, error) {
	var item models.Campus
	err := r.pool.QueryRow(ctx, `
		SELECT id, building_id, name, floor
		FROM campuses
		WHERE id = $1
	`, id).Scan(&item.ID, &item.BuildingID, &item.Name, &item.Floor)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateCampus(ctx context.Context, input models.CampusCreateRequest) (*models.Campus, error) {
	var item models.Campus
	err := r.pool.QueryRow(ctx, `
		INSERT INTO campuses (building_id, name, floor)
		VALUES ($1, $2, $3)
		RETURNING id, building_id, name, floor
	`, input.BuildingID, input.Name, input.Floor).
		Scan(&item.ID, &item.BuildingID, &item.Name, &item.Floor)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateCampus(ctx context.Context, id int32, input models.CampusUpdateRequest) (*models.Campus, error) {
	var item models.Campus
	err := r.pool.QueryRow(ctx, `
		UPDATE campuses
		SET building_id = $2, name = $3, floor = $4
		WHERE id = $1
		RETURNING id, building_id, name, floor
	`, id, input.BuildingID, input.Name, input.Floor).
		Scan(&item.ID, &item.BuildingID, &item.Name, &item.Floor)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteCampus(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "campuses", id)
}

func (r *Repository) ListRooms(ctx context.Context, campusID *int32) ([]models.Room, error) {
	query := `
		SELECT id, campus_id, name, capacity
		FROM rooms
	`
	args := []any{}
	if campusID != nil {
		query += ` WHERE campus_id = $1`
		args = append(args, *campusID)
	}
	query += ` ORDER BY name, id`
	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Room, error) {
		var item models.Room
		err := row.Scan(&item.ID, &item.CampusID, &item.Name, &item.Capacity)
		return item, err
	})
}

func (r *Repository) GetRoom(ctx context.Context, id int32) (*models.Room, error) {
	var item models.Room
	err := r.pool.QueryRow(ctx, `
		SELECT id, campus_id, name, capacity
		FROM rooms
		WHERE id = $1
	`, id).Scan(&item.ID, &item.CampusID, &item.Name, &item.Capacity)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateRoom(ctx context.Context, input models.RoomCreateRequest) (*models.Room, error) {
	var item models.Room
	err := r.pool.QueryRow(ctx, `
		INSERT INTO rooms (campus_id, name, capacity)
		VALUES ($1, $2, $3)
		RETURNING id, campus_id, name, capacity
	`, input.CampusID, input.Name, input.Capacity).
		Scan(&item.ID, &item.CampusID, &item.Name, &item.Capacity)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateRoom(ctx context.Context, id int32, input models.RoomUpdateRequest) (*models.Room, error) {
	var item models.Room
	err := r.pool.QueryRow(ctx, `
		UPDATE rooms
		SET campus_id = $2, name = $3, capacity = $4
		WHERE id = $1
		RETURNING id, campus_id, name, capacity
	`, id, input.CampusID, input.Name, input.Capacity).
		Scan(&item.ID, &item.CampusID, &item.Name, &item.Capacity)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteRoom(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "rooms", id)
}

func (r *Repository) ListDirections(ctx context.Context) ([]models.Direction, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, name, code, department_id
		FROM directions
		ORDER BY code, id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Direction, error) {
		var item models.Direction
		err := row.Scan(&item.ID, &item.Name, &item.Code, &item.DepartmentID)
		return item, err
	})
}

func (r *Repository) GetDirection(ctx context.Context, id int32) (*models.Direction, error) {
	var item models.Direction
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, code, department_id
		FROM directions
		WHERE id = $1
	`, id).Scan(&item.ID, &item.Name, &item.Code, &item.DepartmentID)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateDirection(ctx context.Context, input models.DirectionCreateRequest) (*models.Direction, error) {
	var item models.Direction
	err := r.pool.QueryRow(ctx, `
		INSERT INTO directions (name, code, department_id)
		VALUES ($1, $2, $3)
		RETURNING id, name, code, department_id
	`, input.Name, input.Code, input.DepartmentID).
		Scan(&item.ID, &item.Name, &item.Code, &item.DepartmentID)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateDirection(ctx context.Context, id int32, input models.DirectionUpdateRequest) (*models.Direction, error) {
	var item models.Direction
	err := r.pool.QueryRow(ctx, `
		UPDATE directions
		SET name = $2, code = $3, department_id = $4
		WHERE id = $1
		RETURNING id, name, code, department_id
	`, id, input.Name, input.Code, input.DepartmentID).
		Scan(&item.ID, &item.Name, &item.Code, &item.DepartmentID)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteDirection(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "directions", id)
}

func (r *Repository) ListGroups(ctx context.Context, filter models.GroupFilter) ([]models.Group, error) {
	query := `
		SELECT id, name, admission_year, study_form, direction_id, stream
		FROM groups
	`
	conditions := []string{}
	args := []any{}
	if filter.DirectionID != nil {
		args = append(args, *filter.DirectionID)
		conditions = append(conditions, "direction_id = $1")
	}
	if filter.AdmissionYear != nil {
		args = append(args, *filter.AdmissionYear)
		conditions = append(conditions, placeholder("admission_year = ", len(args)))
	}
	if len(conditions) > 0 {
		query += " WHERE " + strings.Join(conditions, " AND ")
	}
	query += " ORDER BY name, id"

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Group, error) {
		var item models.Group
		err := row.Scan(&item.ID, &item.Name, &item.AdmissionYear, &item.StudyForm, &item.DirectionID, &item.Stream)
		return item, err
	})
}

func (r *Repository) GetGroup(ctx context.Context, id int32) (*models.Group, error) {
	var item models.Group
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, admission_year, study_form, direction_id, stream
		FROM groups
		WHERE id = $1
	`, id).Scan(&item.ID, &item.Name, &item.AdmissionYear, &item.StudyForm, &item.DirectionID, &item.Stream)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateGroup(ctx context.Context, input models.GroupCreateRequest) (*models.Group, error) {
	var item models.Group
	err := r.pool.QueryRow(ctx, `
		INSERT INTO groups (name, admission_year, study_form, direction_id, stream)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id, name, admission_year, study_form, direction_id, stream
	`, input.Name, input.AdmissionYear, input.StudyForm, input.DirectionID, input.Stream).
		Scan(&item.ID, &item.Name, &item.AdmissionYear, &item.StudyForm, &item.DirectionID, &item.Stream)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateGroup(ctx context.Context, id int32, input models.GroupUpdateRequest) (*models.Group, error) {
	var item models.Group
	err := r.pool.QueryRow(ctx, `
		UPDATE groups
		SET name = $2, admission_year = $3, study_form = $4, direction_id = $5, stream = $6
		WHERE id = $1
		RETURNING id, name, admission_year, study_form, direction_id, stream
	`, id, input.Name, input.AdmissionYear, input.StudyForm, input.DirectionID, input.Stream).
		Scan(&item.ID, &item.Name, &item.AdmissionYear, &item.StudyForm, &item.DirectionID, &item.Stream)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteGroup(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "groups", id)
}

func (r *Repository) ListSubjects(ctx context.Context) ([]models.Subject, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, name, short_name
		FROM subjects
		ORDER BY name, id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.Subject, error) {
		var item models.Subject
		err := row.Scan(&item.ID, &item.Name, &item.ShortName)
		return item, err
	})
}

func (r *Repository) GetSubject(ctx context.Context, id int32) (*models.Subject, error) {
	var item models.Subject
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, short_name
		FROM subjects
		WHERE id = $1
	`, id).Scan(&item.ID, &item.Name, &item.ShortName)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateSubject(ctx context.Context, input models.SubjectCreateRequest) (*models.Subject, error) {
	var item models.Subject
	err := r.pool.QueryRow(ctx, `
		INSERT INTO subjects (name, short_name)
		VALUES ($1, $2)
		RETURNING id, name, short_name
	`, input.Name, normalizeNullableString(input.ShortName)).
		Scan(&item.ID, &item.Name, &item.ShortName)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateSubject(ctx context.Context, id int32, input models.SubjectUpdateRequest) (*models.Subject, error) {
	var item models.Subject
	err := r.pool.QueryRow(ctx, `
		UPDATE subjects
		SET name = $2, short_name = $3
		WHERE id = $1
		RETURNING id, name, short_name
	`, id, input.Name, normalizeNullableString(input.ShortName)).
		Scan(&item.ID, &item.Name, &item.ShortName)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteSubject(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "subjects", id)
}

func (r *Repository) ListSubjectTypes(ctx context.Context) ([]models.SubjectType, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, name, short_name, is_online
		FROM subject_types
		ORDER BY name, id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return pgx.CollectRows(rows, func(row pgx.CollectableRow) (models.SubjectType, error) {
		var item models.SubjectType
		err := row.Scan(&item.ID, &item.Name, &item.ShortName, &item.IsOnline)
		return item, err
	})
}

func (r *Repository) GetSubjectType(ctx context.Context, id int32) (*models.SubjectType, error) {
	var item models.SubjectType
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, short_name, is_online
		FROM subject_types
		WHERE id = $1
	`, id).Scan(&item.ID, &item.Name, &item.ShortName, &item.IsOnline)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) CreateSubjectType(ctx context.Context, input models.SubjectTypeCreateRequest) (*models.SubjectType, error) {
	var item models.SubjectType
	err := r.pool.QueryRow(ctx, `
		INSERT INTO subject_types (name, short_name, is_online)
		VALUES ($1, $2, $3)
		RETURNING id, name, short_name, is_online
	`, input.Name, normalizeNullableString(input.ShortName), input.IsOnline).
		Scan(&item.ID, &item.Name, &item.ShortName, &item.IsOnline)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) UpdateSubjectType(ctx context.Context, id int32, input models.SubjectTypeUpdateRequest) (*models.SubjectType, error) {
	var item models.SubjectType
	err := r.pool.QueryRow(ctx, `
		UPDATE subject_types
		SET name = $2, short_name = $3, is_online = $4
		WHERE id = $1
		RETURNING id, name, short_name, is_online
	`, id, input.Name, normalizeNullableString(input.ShortName), input.IsOnline).
		Scan(&item.ID, &item.Name, &item.ShortName, &item.IsOnline)
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *Repository) DeleteSubjectType(ctx context.Context, id int32) error {
	return deleteByID(ctx, r.pool, "subject_types", id)
}

func deleteByID(ctx context.Context, pool *pgxpool.Pool, table string, id int32) error {
	commandTag, err := pool.Exec(ctx, "DELETE FROM "+table+" WHERE id = $1", id)
	if err != nil {
		return err
	}
	if commandTag.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

func normalizeNullableString(value *string) *string {
	if value == nil {
		return nil
	}
	trimmed := strings.TrimSpace(*value)
	if trimmed == "" {
		return nil
	}
	return &trimmed
}

func placeholder(prefix string, index int) string {
	return prefix + "$" + strconv.Itoa(index)
}
