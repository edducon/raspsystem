package rooms

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Удаление аудитории
// @Description Удаление аудитории из системы по её идентификатору
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Param room_uuid path string true "Идентификатор аудитории"
// @Success 200 {object} models.ResponseAPI{result=models.RoomResponse} "Аудитория успешно удалена"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Аудитория не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при удалении Аудитории"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms/{room_uuid} [delete]
func (h *RoomsHandler) DeleteRoom(ctx *gin.Context) {
	roomUUID := ctx.Param("room_uuid")

	deleteError := h.service.RoomsService.DeleteRoom(roomUUID)
	if deleteError != nil {
		messageError := fmt.Sprintf("Error delete room: %s", deleteError.Error())
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
		Message:   "Delete room",
		Result: models.RoomResponse{
			RoomUUID: roomUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
