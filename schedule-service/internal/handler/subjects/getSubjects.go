package subjects

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

// @Summary Получение дисциплин
// @Description Получение списка всех дисциплин в системе
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.Subject} "Данные о дисциплинах успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects [get]
func (h *SubjectsHandler) GetAllSubjects(ctx *gin.Context) {
	GetAllSubjects, GetAllSubjectsError := h.service.SubjectsService.GetAllSubjects()

	if GetAllSubjectsError != nil {
		messageError := fmt.Sprintf("Error get list subjects: %s", GetAllSubjectsError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list subjects",
		Result:    GetAllSubjects,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение дисциплины по её названию
// @Description Получение информации о дисциплине по её subject_name
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Param subject_name path string true "Название дисциплины"
// @Success 200 {object} models.ResponseAPI{result=[]models.Subject} "Данные о дисциплине успешно получены"
// @Failure 404 {object} models.ResponseAPI "Дисциплина не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects/name/{subject_name} [get]
func (h *SubjectsHandler) GetSubjectsByName(ctx *gin.Context) {
	subjectName := ctx.Param("subject_name")
	getSubject, getSubjectError := h.service.SubjectsService.GetSubjectsByName(strings.TrimSpace(subjectName))
	if getSubjectError != nil {
		if errors.Is(getSubjectError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Subject not found: %s", subjectName)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get subject %s: %s", subjectName, getSubjectError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get subject",
		Result:    getSubject,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение дисциплины по идентификатору
// @Description Получение информации о дисциплине по её subject_uuid
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Param subject_uuid path string true "Идентификатор дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.Subject} "Данные о дисциплине успешно получены"
// @Failure 404 {object} models.ResponseAPI "Дисциплина не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects/uuid/{subject_uuid} [get]
func (h *SubjectsHandler) GetSubjectByUUID(ctx *gin.Context) {
	subjectUUID := ctx.Param("subject_uuid")
	getSubject, getSubjectError := h.service.SubjectsService.GetSubjectByUUID(subjectUUID)
	if getSubjectError != nil {
		if errors.Is(getSubjectError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Subject not found: %s", subjectUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get subject: %s", subjectUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get subject",
		Result:    getSubject,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
