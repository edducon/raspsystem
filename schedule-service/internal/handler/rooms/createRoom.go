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

// @Summary Добавление аудитории
// @Description Создание новой аудитории
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Param request body models.AddRoomRequest true "Данные новой аудитории"
// @Success 201 {object} models.ResponseAPI{result=models.RoomResponse} "Аудитория успешно создана"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании аудитории"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms [post]
func (h *RoomsHandler) CreateRoom(ctx *gin.Context) {
	var request models.AddRoomRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing room data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.Number = strings.TrimSpace(request.Number)

	createRoomUUID, createRoomError := h.service.RoomsService.CreateRoom(&request)
	if createRoomError != nil {
		messageError := fmt.Sprintf("Error new room: %s", createRoomError.Error())
		if strings.Contains(createRoomError.Error(), "already exists") {
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
		Message:   "Add new room",
		Result: models.RoomResponse{
			RoomUUID: createRoomUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
