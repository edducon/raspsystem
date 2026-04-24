package subjects

import (
	"database/sql"
	"errors"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
)

// @Summary Обновление дисциплины
// @Description Обновление информации о дисциплине по её идентификатору
// @Security ApiKeyAuth
// @Tags subjects
// @Accept application/json
// @Produce application/json
// @Param subject_uuid path string true "Идентификатор дисциплины"
// @Param request body models.UpdateSubjectRequest true "Данные для обновления дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.SubjectResponse} "Данные о дисциплине успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Дисциплина не найдена"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subjects/{subject_uuid} [put]
func (h *SubjectsHandler) UpdateSubject(ctx *gin.Context) {
	var request models.UpdateSubjectRequest

	subjectUUID := ctx.Param("subject_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing subject data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.SubjectsService.UpdateSubject(subjectUUID, &request)
	if updateError != nil {
		messageError := "Error update subject: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", subjectUUID)
			logger.NewErrorResponse(ctx, h.log, true, http.StatusNotFound, messageError)
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
		Message:   "Update subject",
		Result: models.SubjectResponse{
			SubjectUUID: subjectUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
