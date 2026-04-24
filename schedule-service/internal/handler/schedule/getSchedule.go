package schedule

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

// @Summary Получение расписания по номеру группы
// @Description Получение информации о расписании по его group_number
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param group_number path string true "Номер учебной группы"
// @Param is_session query bool false "Флаг сессии"
// @Success 200 {object} models.ResponseAPI{result=models.Week} "Данные о расписании успешно получены"
// @Failure 404 {object} models.ResponseAPI "Расписание не найдено"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/group_number/{group_number} [get]
func (h *ScheduleHandler) GetScheduleByGroupNumber(ctx *gin.Context) {
	groupNumber := ctx.Param("group_number")
	var params models.GetScheduleByGroupNumberParams
	messageError := "Error get schedule: "
	if err := ctx.ShouldBindQuery(&params); err != nil {
		messageError += fmt.Sprintf("error parsing params: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	getSchedule, getScheduleError := h.service.ScheduleService.GetScheduleByGroupNumber(groupNumber, params.IsSession) // TODO: Сделать query параметр is_session
	if getScheduleError != nil {
		if errors.Is(getScheduleError, sql.ErrNoRows) || strings.Contains(getScheduleError.Error(), "not found") {
			messageError += fmt.Sprintf("schedule for group %q not found", groupNumber)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
		} else {
			messageError += fmt.Sprintf("%s: %s", groupNumber, getScheduleError)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get schedule",
		Result:    getSchedule,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение расписания по ФИО преподавателя
// @Description Получение информации о расписании по его teacher_fio
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param teacher_fio path string true "ФИО преподавателя"
// @Param is_session query bool false "Флаг сессии"
// @Success 200 {object} models.ResponseAPI{result=models.Week} "Данные о расписании успешно получены"
// @Failure 404 {object} models.ResponseAPI "Расписание не найдено"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/teacher_fio/{teacher_fio} [get]
func (h *ScheduleHandler) GetScheduleByTeacherFio(ctx *gin.Context) {
	teacherFio := ctx.Param("teacher_fio")
	var params models.GetScheduleByTeacherFioParams
	messageError := "Error get schedule: "
	if err := ctx.ShouldBindQuery(&params); err != nil {
		messageError += fmt.Sprintf("error parsing params: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	getSchedule, getScheduleError := h.service.ScheduleService.GetScheduleByTeacherFio(teacherFio, params.IsSession)
	if getScheduleError != nil {
		if errors.Is(getScheduleError, sql.ErrNoRows) || strings.Contains(getScheduleError.Error(), "not found") {
			messageError += fmt.Sprintf("schedule for teacher %q not found", teacherFio)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
		} else if strings.Contains(getScheduleError.Error(), "teacher") {
			messageError += getScheduleError.Error()
			logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		} else {
			messageError += fmt.Sprintf("%s: %s", teacherFio, getScheduleError)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get schedule",
		Result:    getSchedule,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
// @Summary Получение расписания по названию локации
// @Description Получение информации о расписании по его location_name (корпусу)
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param location_name path string true "Название локации (корпуса)"
// @Param is_session query bool false "Флаг сессии"
// @Success 200 {object} models.ResponseAPI{result=models.Week} "Данные о расписании успешно получены"
// @Failure 404 {object} models.ResponseAPI "Расписание не найдено"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/location_name/{location_name} [get]
func (h *ScheduleHandler) GetScheduleByLocationName(ctx *gin.Context) {
    locationName := ctx.Param("location_name")

    // Используем структуру параметров от группы, так как нам нужен только флаг is_session
    var params models.GetScheduleByGroupNumberParams
    messageError := "Error get schedule: "
    if err := ctx.ShouldBindQuery(&params); err != nil {
       messageError += fmt.Sprintf("error parsing params: %s", err.Error())
       logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
       return
    }

    // Вызываем сервис локации
    getSchedule, getScheduleError := h.service.ScheduleService.GetScheduleByLocationName(locationName, params.IsSession)

    if getScheduleError != nil {
       if errors.Is(getScheduleError, sql.ErrNoRows) || strings.Contains(getScheduleError.Error(), "not found") {
          messageError += fmt.Sprintf("schedule for location %q not found", locationName)
          logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
       } else {
          messageError += fmt.Sprintf("%s: %s", locationName, getScheduleError)
          logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
       }
       return
    }

    currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

    responseApi := &models.ResponseAPI{
       Success:   true,
       RequestId: fmt.Sprint(currentRequestId),
       Message:   "Get schedule",
       Result:    getSchedule,
    }

    h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

    ctx.JSON(http.StatusOK, responseApi)
}
// @Summary Получение всего расписания
// @Description Получение полного расписания (списком) по всему университету
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param is_session query bool false "Флаг сессии"
// @Success 200 {object} models.ResponseAPI{result=[]models.GetSchedule} "Данные о расписании успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/all [get]
func (h *ScheduleHandler) GetAllSchedule(ctx *gin.Context) {
	// Используем существующую структуру для парсинга is_session
	var params models.GetScheduleByGroupNumberParams
	messageError := "Error get all schedule: "
	if err := ctx.ShouldBindQuery(&params); err != nil {
		messageError += fmt.Sprintf("error parsing params: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	getSchedule, getScheduleError := h.service.ScheduleService.GetAllSchedule(params.IsSession)

	if getScheduleError != nil {
		messageError += getScheduleError.Error()
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get all schedule",
		Result:    getSchedule, // Возвращаем плоский массив напрямую
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}