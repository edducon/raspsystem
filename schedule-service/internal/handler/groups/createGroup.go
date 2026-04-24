package groups

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление учебной группы
// @Description Создание новой учебной группы
// @Security ApiKeyAuth
// @Tags groups
// @Accept application/json
// @Produce application/json
// @Param request body models.AddGroupRequest true "Данные новой учебной группы"
// @Success 201 {object} models.ResponseAPI{result=models.GroupResponse} "Учебная группа успешно создана"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании учебной группы"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/groups [post]
func (h *GroupsHandler) CreateGroup(ctx *gin.Context) {
	var request models.AddGroupRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing group data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.Number = strings.TrimSpace(request.Number)

	createGroupUUID, createGroupError := h.service.GroupsService.CreateGroup(&request)
	if createGroupError != nil {
		messageError := fmt.Sprintf("Error new group: %s", createGroupError.Error())
		if strings.Contains(createGroupError.Error(), "already exists") {
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
		Message:   "Add new group",
		Result: models.GroupResponse{
			GroupUUID: createGroupUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
