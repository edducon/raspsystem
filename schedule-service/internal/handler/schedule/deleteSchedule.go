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

// @Summary Удаление расписания
// @Description Удаление расписания из системы по его идентификатору
// @Security ApiKeyAuth
// @Tags schedule
// @Accept application/json
// @Produce application/json
// @Param schedule_uuid path string true "Идентификатор расписания"
// @Success 200 {object} models.ResponseAPI{result=models.ScheduleResponse} "Расписание успешно удалено"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Расписание не найдено"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении расписания"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/schedule/{schedule_uuid} [delete]
func (h *ScheduleHandler) DeleteSchedule(ctx *gin.Context) {
	scheduleUUID := ctx.Param("schedule_uuid")

	deleteError := h.service.ScheduleService.DeleteSchedule(scheduleUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete schedule: %s", deleteError.Error())
		if strings.Contains(deleteError.Error(), "not found") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
		} else if strings.Contains(deleteError.Error(), "it is being referenced") {
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
		Message:   "Delete schedule",
		Result: models.ScheduleResponse{
			ScheduleUUID: scheduleUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
