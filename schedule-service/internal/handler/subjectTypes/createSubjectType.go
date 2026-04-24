package subjectTypes

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление типа дисциплины
// @Description Создание нового типа дисциплины
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Param request body models.AddSubjectTypeRequest true "Данные нового типа дисциплины"
// @Success 201 {object} models.ResponseAPI{result=models.SubjectTypeResponse} "Тип дисциплины успешно создан"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании типа дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types [post]
func (h *SubjectTypesHandler) CreateSubjectType(ctx *gin.Context) {
	var request models.AddSubjectTypeRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing subject type data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.Type = strings.TrimSpace(request.Type)

	createSubjectTypeUUID, createSubjectTypeError := h.service.SubjectTypesService.CreateSubjectType(&request)
	if createSubjectTypeError != nil {
		messageError := fmt.Sprintf("Error new subject type: %s", createSubjectTypeError.Error())
		if strings.Contains(createSubjectTypeError.Error(), "already exists") {
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
		Message:   "Add new subject type",
		Result: models.SubjectTypeResponse{
			SubjectTypeUUID: createSubjectTypeUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
