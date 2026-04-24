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

// @Summary Обновление расписания
// @Description Обновление информации о расписании по его идентификатору
// @Security ApiKeyAuth
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param schedule_uuid path string true "Идентификатор расписания"
// @Param request body models.UpdateScheduleRequest true "Данные для обновления расписания"
// @Success 200 {object} models.ResponseAPI{result=models.ScheduleResponse} "Данные о расписании успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Расписание не найдено"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении расписания"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/{schedule_uuid} [put]
func (h *ScheduleHandler) UpdateSchedule(ctx *gin.Context) {
	var request models.UpdateScheduleRequest

	scheduleUUID := ctx.Param("schedule_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing schedule data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.ScheduleService.UpdateSchedule(scheduleUUID, &request)
	if updateError != nil {
		messageError := "Error update schedule: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", scheduleUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
		} else if strings.Contains(updateError.Error(), "foreign") {
			messageError += updateError.Error()
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
		} else {
			messageError += updateError.Error()
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Update schedule",
		Result: models.ScheduleResponse{
			ScheduleUUID: scheduleUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
