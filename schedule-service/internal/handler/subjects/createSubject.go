package subjects

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление дисциплины
// @Description Создание новой дисциплины
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Param request body models.AddSubjectRequest true "Данные новой дисциплины"
// @Success 201 {object} models.ResponseAPI{result=models.SubjectResponse} "Дисциплина успешно создана"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects [post]
func (h *SubjectsHandler) CreateSubject(ctx *gin.Context) {
	var request models.AddSubjectRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing subject data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.Name = strings.TrimSpace(request.Name)

	createSubjectUUID, createSubjectError := h.service.SubjectsService.CreateSubject(&request)
	if createSubjectError != nil {
		messageError := fmt.Sprintf("Error new subject: %s", createSubjectError.Error())
		if strings.Contains(createSubjectError.Error(), "already exists") {
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
		Message:   "Add new subject",
		Result: models.SubjectResponse{
			SubjectUUID: createSubjectUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
