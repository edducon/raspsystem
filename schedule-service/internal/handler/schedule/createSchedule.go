package schedule

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление расписания
// @Description Создание нового расписания
// @Security ApiKeyAuth
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param request body models.AddScheduleRequest true "Данные нового расписания"
// @Success 201 {object} models.ResponseAPI{result=models.ScheduleResponse} "Расписание успешно создано"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании расписания"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule [post]
func (h *ScheduleHandler) CreateSchedule(ctx *gin.Context) {
	var request models.AddScheduleRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing schedule data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	createScheduleUUID, createScheduleError := h.service.ScheduleService.CreateSchedule(&request)
	if createScheduleError != nil {
		messageError := fmt.Sprintf("Error new schedule: %s", createScheduleError.Error())
		if strings.Contains(createScheduleError.Error(), "foreign") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
		} else {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Add new schedule",
		Result: models.ScheduleResponse{
			ScheduleUUID: createScheduleUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
