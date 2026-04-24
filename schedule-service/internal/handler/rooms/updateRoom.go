package rooms

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

// @Summary Обновление аудитории
// @Description Обновление информации об аудитории по её идентификатору
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Param room_uuid path string true "Идентификатор аудитории"
// @Param request body models.UpdateRoomRequest true "Данные для обновления аудитории"
// @Success 200 {object} models.ResponseAPI{result=models.RoomResponse} "Данные об аудитории успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Аудитория не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении аудитории"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms/{room_uuid} [put]
func (h *RoomsHandler) UpdateRoom(ctx *gin.Context) {
	var request models.UpdateRoomRequest

	roomUUID := ctx.Param("room_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing room data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.RoomsService.UpdateRoom(roomUUID, &request)
	if updateError != nil {
		messageError := "Error update room: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", roomUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		} else if strings.Contains(updateError.Error(), "already exists") {
			messageError += "target room already exists"
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
			return
		}
		messageError += updateError.Error()
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Update room",
		Result: models.RoomResponse{
			RoomUUID: roomUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
