package catalog

import (
	"errors"
	"log/slog"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"

	"raspyx2/internal/models"
	"raspyx2/internal/service"
)

type Handler struct {
	log     *slog.Logger
	service *service.Service
}

func NewHandler(log *slog.Logger, service *service.Service) *Handler {
	return &Handler{log: log, service: service}
}

func (h *Handler) ListBuildings(ctx *gin.Context) {
	items, err := h.service.ListBuildings(ctx.Request.Context())
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetBuilding(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetBuilding(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateBuilding(ctx *gin.Context) {
	var input models.BuildingCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateBuilding(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateBuilding(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.BuildingUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateBuilding(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteBuilding(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteBuilding(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListCampuses(ctx *gin.Context) {
	items, err := h.service.ListCampuses(ctx.Request.Context(), parseOptionalInt32(ctx.Query("building_id")))
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetCampus(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetCampus(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateCampus(ctx *gin.Context) {
	var input models.CampusCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateCampus(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateCampus(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.CampusUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateCampus(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteCampus(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteCampus(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListRooms(ctx *gin.Context) {
	items, err := h.service.ListRooms(ctx.Request.Context(), parseOptionalInt32(ctx.Query("campus_id")))
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetRoom(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetRoom(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateRoom(ctx *gin.Context) {
	var input models.RoomCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateRoom(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateRoom(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.RoomUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateRoom(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteRoom(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteRoom(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListDirections(ctx *gin.Context) {
	items, err := h.service.ListDirections(ctx.Request.Context())
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetDirection(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetDirection(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateDirection(ctx *gin.Context) {
	var input models.DirectionCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateDirection(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateDirection(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.DirectionUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateDirection(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteDirection(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteDirection(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListGroups(ctx *gin.Context) {
	filter := models.GroupFilter{
		DirectionID:   parseOptionalInt32(ctx.Query("direction_id")),
		AdmissionYear: parseOptionalInt16(ctx.Query("admission_year")),
	}
	items, err := h.service.ListGroups(ctx.Request.Context(), filter)
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetGroup(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetGroup(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateGroup(ctx *gin.Context) {
	var input models.GroupCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateGroup(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateGroup(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.GroupUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateGroup(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteGroup(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteGroup(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListSubjects(ctx *gin.Context) {
	items, err := h.service.ListSubjects(ctx.Request.Context())
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetSubject(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetSubject(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateSubject(ctx *gin.Context) {
	var input models.SubjectCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateSubject(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateSubject(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.SubjectUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateSubject(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteSubject(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteSubject(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) ListSubjectTypes(ctx *gin.Context) {
	items, err := h.service.ListSubjectTypes(ctx.Request.Context())
	h.respond(ctx, http.StatusOK, items, err)
}

func (h *Handler) GetSubjectType(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	item, err := h.service.GetSubjectType(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) CreateSubjectType(ctx *gin.Context) {
	var input models.SubjectTypeCreateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.CreateSubjectType(ctx.Request.Context(), input)
	h.respond(ctx, http.StatusCreated, item, err)
}

func (h *Handler) UpdateSubjectType(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	var input models.SubjectTypeUpdateRequest
	if !h.bindJSON(ctx, &input) {
		return
	}
	item, err := h.service.UpdateSubjectType(ctx.Request.Context(), id, input)
	h.respond(ctx, http.StatusOK, item, err)
}

func (h *Handler) DeleteSubjectType(ctx *gin.Context) {
	id, ok := h.parseID(ctx)
	if !ok {
		return
	}
	err := h.service.DeleteSubjectType(ctx.Request.Context(), id)
	h.respond(ctx, http.StatusNoContent, nil, err)
}

func (h *Handler) parseID(ctx *gin.Context) (int32, bool) {
	value, err := strconv.ParseInt(ctx.Param("id"), 10, 32)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "id must be an integer"})
		return 0, false
	}
	return int32(value), true
}

func (h *Handler) bindJSON(ctx *gin.Context, target any) bool {
	if err := ctx.ShouldBindJSON(target); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return false
	}
	return true
}

func (h *Handler) respond(ctx *gin.Context, successStatus int, payload any, err error) {
	if err != nil {
		statusCode, message := mapError(err)
		h.log.Error("catalog handler error", slog.Int("status", statusCode), slog.String("error", err.Error()))
		ctx.JSON(statusCode, gin.H{"error": message})
		return
	}

	if successStatus == http.StatusNoContent {
		ctx.Status(http.StatusNoContent)
		return
	}

	ctx.JSON(successStatus, payload)
}

func mapError(err error) (int, string) {
	if errors.Is(err, pgx.ErrNoRows) {
		return http.StatusNotFound, "resource not found"
	}

	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		switch pgErr.Code {
		case "23505":
			return http.StatusConflict, "resource already exists"
		case "23503":
			return http.StatusBadRequest, "invalid foreign key reference"
		case "23514":
			return http.StatusBadRequest, "constraint violation"
		}
	}

	return http.StatusInternalServerError, "internal server error"
}

func parseOptionalInt32(value string) *int32 {
	if value == "" {
		return nil
	}
	parsed, err := strconv.ParseInt(value, 10, 32)
	if err != nil {
		return nil
	}
	converted := int32(parsed)
	return &converted
}

func parseOptionalInt16(value string) *int16 {
	if value == "" {
		return nil
	}
	parsed, err := strconv.ParseInt(value, 10, 16)
	if err != nil {
		return nil
	}
	converted := int16(parsed)
	return &converted
}
