package teachers

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"raspyx2/internal/handler/constHandler"
	"raspyx2/internal/models"
	"raspyx2/pkg/logger"
	"strings"
)

// @Summary Добавление преподавателя
// @Description Создание нового преподавателя
// @Security ApiKeyAuth
// @Tags teachers
// @Accept application/json
// @Produce application/json
// @Param request body models.AddTeacherRequest true "Данные нового преподавателя"
// @Success 201 {object} models.ResponseAPI{result=models.TeacherResponse} "Преподаватель создана"
// @Failure 400 {object} models.ResponseAPI "Неверный формат запроса"
// @Failure 409 {object} models.ResponseAPI "Конфликт при создании преподавателя"
// @Failure 500 {object} models.ResponseAPI "Внутренняя ошибка сервера"
// @Router /v2/teachers [post]
func (h *TeachersHandler) CreateTeacher(ctx *gin.Context) {
	var request models.AddTeacherRequest

	if err := ctx.ShouldBindJSON(&request); err != nil {
		messageError := fmt.Sprintf("Error parsing teacher data: %s", err.Error())
		logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		return
	}

	request.FirstName = strings.TrimSpace(request.FirstName)
	request.SecondName = strings.TrimSpace(request.SecondName)
	request.MiddleName = strings.TrimSpace(request.MiddleName)

	createTeacherUUID, createTeacherError := h.service.TeachersService.CreateTeacher(&request)
	if createTeacherError != nil {
		messageError := fmt.Sprintf("Error new teacher: %s", createTeacherError.Error())
		if strings.Contains(createTeacherError.Error(), "already exists") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusConflict, messageError)
		} else if strings.Contains(createTeacherError.Error(), "required") {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusBadRequest, messageError)
		} else {
			logger.NewErrorResponse(ctx, h.log, true, http.StatusInternalServerError, messageError)
		}
		return
	}

	currentRequestId, _ := ctx.Get(constHandler.REQUEST_ID)
	responseApi := &models.ResponseAPI{
		Success:   true,
		RequestId: fmt.Sprint(currentRequestId),
		Message:   "Add new teacher",
		Result: models.TeacherResponse{
			TeacherUUID: createTeacherUUID,
		},
	}

	h.log.Debug(fmt.Sprintf("response %s: %+v", ctx.Request.URL.Path, responseApi))

	ctx.JSON(http.StatusCreated, responseApi)
}
