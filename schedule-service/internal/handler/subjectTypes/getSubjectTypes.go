package subjectTypes

import (
	"database/sql"
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Получение типов дисциплины
// @Description Получение списка всех типов дисциплины в системе
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.SubjectType} "Данные о типах дисциплины успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types [get]
func (h *SubjectTypesHandler) GetAllSubjectTypes(ctx *gin.Context) {
	GetAllSubjectTypes, GetAllSubjectTypesError := h.service.SubjectTypesService.GetAllSubjectTypes()

	if GetAllSubjectTypesError != nil {
		messageError := fmt.Sprintf("Error get list subject types: %s", GetAllSubjectTypesError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list subject types",
		Result:    GetAllSubjectTypes,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение типа дисциплины по его типу
// @Description Получение информации о типе дисциплины по его subject_type
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Param subject_type path string true "Название типа дисциплины"
// @Success 200 {object} models.ResponseAPI{result=[]models.SubjectType} "Данные о типе дисциплины успешно получены"
// @Failure 404 {object} models.ResponseAPI "Тип дисциплины не найден"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types/type/{subject_type} [get]
func (h *SubjectTypesHandler) GetSubjectTypesByType(ctx *gin.Context) {
	subjectType := ctx.Param("subject_type")
	getSubjectType, getSubjectTypeError := h.service.SubjectTypesService.GetSubjectTypesByType(strings.TrimSpace(subjectType))
	if getSubjectTypeError != nil {
		if errors.Is(getSubjectTypeError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Subject type not found: %s", subjectType)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get subject type %s: %s", subjectType, getSubjectTypeError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get subject type",
		Result:    getSubjectType,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение типа дисциплины по идентификатору
// @Description Получение информации о типе дисциплины по его subject_type_uuid
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Param subject_type_uuid path string true "Идентификатор типа дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.SubjectType} "Данные о типе дисциплины успешно получены"
// @Failure 404 {object} models.ResponseAPI "Тип дисциплины не найден"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types/uuid/{subject_type_uuid} [get]
func (h *SubjectTypesHandler) GetSubjectTypeByUUID(ctx *gin.Context) {
	subjectTypeUUID := ctx.Param("subject_type_uuid")
	getSubjectType, getSubjectTypeError := h.service.SubjectTypesService.GetSubjectTypeByUUID(subjectTypeUUID)
	if getSubjectTypeError != nil {
		if errors.Is(getSubjectTypeError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Subject type not found: %s", subjectTypeUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get subject type: %s", subjectTypeUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get subject type",
		Result:    getSubjectType,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
