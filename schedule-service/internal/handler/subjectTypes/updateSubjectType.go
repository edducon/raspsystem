package subjectTypes

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

// @Summary Обновление типа дисциплины
// @Description Обновление информации о типе дисциплины по его идентификатору
// @Security ApiKeyAuth
// @Tags subject_types
// @Accept application/json
// @Produce application/json
// @Param subject_type_uuid path string true "Идентификатор типа дисциплины"
// @Param request body models.UpdateSubjectTypeRequest true "Данные для обновления типа дисциплины"
// @Success 200 {object} models.ResponseAPI{result=models.SubjectTypeResponse} "Данные о типе дисциплины успешно обновлены"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 404 {object} models.ResponseAPI "Тип дисциплины не найден"
// @Failure 409 {object} models.ResponseAPI "Конфликт при обновлении типа дисциплины"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/subject_types/{subject_type_uuid} [put]
func (h *SubjectTypesHandler) UpdateSubjectType(ctx *gin.Context) {
	var request models.UpdateSubjectTypeRequest

	subjectTypeUUID := ctx.Param("subject_type_uuid")

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing subject type data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	updateError := h.service.SubjectTypesService.UpdateSubjectType(subjectTypeUUID, &request)
	if updateError != nil {
		messageError := "Error update subject type: "
		if errors.Is(updateError, sql.ErrNoRows) {
			messageError += fmt.Sprintf("%s not found", subjectTypeUUID)
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
		Message:   "Update subject type",
		Result: models.SubjectTypeResponse{
			SubjectTypeUUID: subjectTypeUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusOK, responseApi)
}
