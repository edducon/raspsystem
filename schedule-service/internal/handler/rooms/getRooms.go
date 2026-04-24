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

// @Summary Получение аудиторий
// @Description Получение списка всех аудиторий в системе
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Success 200 {object} models.ResponseAPI{result=[]models.Room} "Данные об аудиториях успешно получены"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms [get]
func (h *RoomsHandler) GetAllRooms(ctx *gin.Context) {
	GetAllRooms, GetAllRoomsError := h.service.RoomsService.GetAllRooms()

	if GetAllRoomsError != nil {
		messageError := fmt.Sprintf("Error get list rooms: %s", GetAllRoomsError.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get list rooms",
		Result:    GetAllRooms,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение аудитории по её номеру
// @Description Получение информации об аудитории по её room_number
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Param room_number path string true "Номер аудитории"
// @Success 200 {object} models.ResponseAPI{result=[]models.Room} "Данные об аудитории успешно получены"
// @Failure 404 {object} models.ResponseAPI "Аудитория не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms/number/{room_number} [get]
func (h *RoomsHandler) GetRoomsByNumber(ctx *gin.Context) {
	roomNumber := ctx.Param("room_number")
	getRoom, getRoomError := h.service.RoomsService.GetRoomsByNumber(strings.TrimSpace(roomNumber))
	if getRoomError != nil {
		if errors.Is(getRoomError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Room not found: %s", roomNumber)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get room %s: %s", roomNumber, getRoomError)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get room",
		Result:    getRoom,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}

// @Summary Получение аудитории по идентификатору
// @Description Получение информации об аудитории по её room_uuid
// @Security ApiKeyAuth
// @Tags rooms
// @Accept application/json
// @Produce application/json
// @Param room_uuid path string true "Идентификатор аудитории"
// @Success 200 {object} models.ResponseAPI{result=models.Room} "Данные об аудитории успешно получены"
// @Failure 404 {object} models.ResponseAPI "Аудитория не найдена"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/rooms/uuid/{room_uuid} [get]
func (h *RoomsHandler) GetRoomByUUID(ctx *gin.Context) {
	roomUUID := ctx.Param("room_uuid")
	getRoom, getRoomError := h.service.RoomsService.GetRoomByUUID(roomUUID)
	if getRoomError != nil {
		if errors.Is(getRoomError, sql.ErrNoRows) {
			messageError := fmt.Sprintf("Room not found: %s", roomUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
			return
		}
		messageError := fmt.Sprintf("Error get room: %s", roomUUID)
		logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)

	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Get room",
		Result:    getRoom,
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
